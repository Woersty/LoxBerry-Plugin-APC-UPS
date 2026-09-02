#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APC-UPS - Ueberwachungsdienst

Fragt in einstellbarem Takt apcaccess ab und veroeffentlicht die Werte
retained per MQTT. Wechselt die USV zwischen Netz- und Akkubetrieb, legt der
Dienst zusaetzlich eine Meldung in den LoxBerry-Benachrichtigungsbereich und
verschickt auf Wunsch eine E-Mail.

Grundlage ist das Plugin von Christian Woerstenfeld (Apache-Lizenz 2.0).
Neu geschrieben fuer LoxBerry 4:

  * Durchlaufender Dienst mit MQTT statt einer Seite, die auf Zuruf
    apcaccess aufruft.
  * apcaccess wird gesucht statt fest unter /sbin erwartet.
  * Ereignisse (Akkubetrieb, Netz zurueck, Kommunikationsverlust) werden im
    Dienst erkannt, nicht mehr ueber Ereignisskripte von apcupsd.
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import apc_common as gem   # noqa: E402

_handlers = []
try:
    os.makedirs(gem.LOG_DIR, exist_ok=True)
    _handlers.append(logging.FileHandler(os.path.join(gem.LOG_DIR, "apc_ups.log")))
except OSError:
    pass
_handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=_handlers,
)
log = logging.getLogger("apc_ups")


class Mqtt:
    """Duenne Huelle um paho-mqtt. Faellt still aus, wenn Bibliothek oder
    Gateway fehlen - der Dienst protokolliert dann weiter."""

    def __init__(self, praefix):
        self.praefix = praefix
        self.client = None

    def start(self):
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            log.error("paho-mqtt fehlt - MQTT bleibt aus. "
                      "Paket python3-paho-mqtt nachinstallieren.")
            return False
        zugang = gem.mqtt_zugangsdaten()
        if not zugang:
            log.warning("Kein MQTT-Broker in general.json gefunden")
            return False
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except (AttributeError, TypeError):
            self.client = mqtt.Client()      # paho-mqtt 1.x
        if zugang["user"]:
            self.client.username_pw_set(zugang["user"], zugang["pass"] or "")
        self.client.will_set(self.praefix + "/service/online", "0", retain=True)
        try:
            self.client.connect(zugang["host"], zugang["port"], keepalive=60)
        except OSError as fehler:
            log.error("MQTT-Broker %s:%s nicht erreichbar: %s",
                      zugang["host"], zugang["port"], fehler)
            return False
        self.client.loop_start()
        log.info("MQTT verbunden mit %s:%s, Themenpräfix %s",
                 zugang["host"], zugang["port"], self.praefix)
        self.senden("service/online", "1")
        return True

    def senden(self, unterthema, wert):
        if not self.client:
            return
        try:
            self.client.publish(self.praefix + "/" + unterthema,
                                "" if wert is None else str(wert),
                                qos=0, retain=True)
        except Exception as fehler:  # noqa: BLE001
            log.error("MQTT-Veröffentlichung fehlgeschlagen: %s", fehler)

    def stop(self):
        if not self.client:
            return
        try:
            self.senden("service/online", "0")
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:  # noqa: BLE001
            pass


def email_senden(betreff, text, empfaenger="root"):
    """E-Mail ueber den oertlichen sendmail verschicken.

    Der Weg der Originalfassung. Ist kein Mailversand eingerichtet, schlaegt
    das still fehl - deshalb die Rueckmeldung, damit es im Protokoll steht.
    """
    for prog in ("/usr/sbin/sendmail", "/usr/lib/sendmail"):
        if os.path.isfile(prog):
            break
    else:
        return False, "sendmail ist auf diesem System nicht vorhanden"
    empfaenger = (empfaenger or "root").strip() or "root"
    nachricht = ("To: {0}\nSubject: {1}\nContent-Type: text/plain; charset=UTF-8\n\n{2}\n"
                 .format(empfaenger, betreff, text))
    try:
        lauf = subprocess.run([prog, "-t"], input=nachricht, text=True,
                              capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as fehler:
        return False, str(fehler)
    if lauf.returncode != 0:
        return False, (lauf.stderr or "").strip()[:200]
    return True, empfaenger


class Dienst:
    def __init__(self):
        self.cfg, alt = gem.konfiguration_lesen()
        if alt:
            log.info("Konfiguration im alten Format erkannt - wird übernommen "
                     "und beim nächsten Speichern neu geschrieben")
        self.praefix = self.cfg.get("themenpraefix") or "apcups"
        self.mqtt = Mqtt(self.praefix)
        self.laeuft = True
        self.letzter_stand = {}
        self.letzter_status = None
        self.config_mtime = self._mtime()
        self._gemeldet = {}

    def _mtime(self):
        try:
            return os.path.getmtime(gem.CONFIG_FILE)
        except OSError:
            return 0

    def _einmal(self, schluessel, text, stufe="error", wieder_nach=3600):
        """Dieselbe Meldung nicht bei jedem Durchgang wiederholen.

        Eine fehlende USV bleibt fehlend. Ohne diese Bremse schriebe der
        Dienst bei 30 Sekunden Takt 2880 gleichlautende Zeilen am Tag.
        """
        jetzt = time.time()
        alt = self._gemeldet.get(schluessel)
        if alt and alt[0] == text and (jetzt - alt[1]) < wieder_nach:
            return False
        self._gemeldet[schluessel] = (text, jetzt)
        getattr(log, stufe)("%s", text)
        return True

    def _senden(self, thema, wert, erzwingen=False):
        wert = "" if wert is None else str(wert)
        if not erzwingen and self.letzter_stand.get(thema) == wert:
            return False
        self.letzter_stand[thema] = wert
        self.mqtt.senden(thema, wert)
        return True

    def zustand_schreiben(self, daten):
        try:
            temp = gem.STATUS_FILE + ".tmp"
            with open(temp, "w", encoding="utf-8") as fh:
                json.dump(daten, fh, ensure_ascii=False)
            os.replace(temp, gem.STATUS_FILE)
            os.chmod(gem.STATUS_FILE, 0o644)
        except OSError as fehler:
            log.warning("Zustandsdatei nicht schreibbar: %s", fehler)

    def ereignis(self, alt, neu, werte):
        """Zustandswechsel melden - einmal je Wechsel, nicht je Durchgang."""
        if alt is None or alt == neu:
            return
        ladung = werte.get("battery_charge")
        rest = werte.get("time_left")
        zusatz = ""
        if ladung is not None:
            zusatz += "  Akku {0:.0f} %".format(ladung)
        if rest is not None:
            zusatz += "  noch {0:.0f} min".format(rest)

        if werte.get("on_battery"):
            titel = "Stromausfall"
            text = "Die USV speist aus dem Akku." + zusatz
            schwere = "error"
        elif alt in ("ONBATT", "LOWBATT", "SHUTTING"):
            titel = "Netz wieder da"
            text = "Die USV ist zurück im Netzbetrieb." + zusatz
            schwere = "info"
        elif "COMMLOST" in neu:
            titel = "Verbindung zur USV verloren"
            text = "apcupsd erreicht die USV nicht mehr."
            schwere = "error"
        else:
            titel = "Zustand geändert"
            text = "Die USV meldet jetzt {0} (vorher {1}).".format(neu, alt)
            schwere = "warning"

        log.warning("%s - %s", titel, text)
        self.mqtt.senden("event", titel)

        if self.cfg.get("benachrichtigung", "1") == "1":
            if not gem.benachrichtigen("{0}: {1}".format(titel, text), schwere):
                log.info("LoxBerry-Benachrichtigung nicht möglich")
        if self.cfg.get("email", "0") == "1":
            ok, wohin = email_senden("APC-UPS: " + titel, text,
                                     self.cfg.get("email_an", "root"))
            log.info("E-Mail an %s verschickt", wohin) if ok else \
                log.warning("E-Mail nicht verschickt: %s", wohin)

    def durchgang(self, erzwingen=False):
        ergebnis = gem.abfragen(self.cfg)
        werte = ergebnis["werte"]

        if werte is None:
            self._einmal("abfrage", ergebnis["fehler"], "warning")
            self._senden("valid", "0", erzwingen)
            self._senden("last_error", ergebnis["fehler"].splitlines()[0], erzwingen)
            self.zustand_schreiben({"zeit": int(time.time()), "version": gem.version(),
                                    "werte": None, "roh": {},
                                    "fehler": ergebnis["fehler"]})
            return

        self._gemeldet.pop("abfrage", None)
        neu = werte["status"]
        self.ereignis(self.letzter_status, neu, werte)
        self.letzter_status = neu

        log.info("%s  Akku %s %%  Rest %s min  Netz %s V  Last %s %%",
                 neu, werte["battery_charge"], werte["time_left"],
                 werte["line_voltage"], werte["load_percent"])

        self._senden("valid", "1", erzwingen)
        self._senden("last_error", "", erzwingen)
        for thema, wert in werte.items():
            self._senden(thema, wert, erzwingen)

        self.zustand_schreiben({
            "zeit": int(time.time()), "version": gem.version(),
            "werte": werte, "roh": ergebnis["roh"], "fehler": "",
        })

    def start(self):
        log.info("APC-UPS %s startet", gem.version())
        log.info("Konfiguration: %s", gem.CONFIG_FILE)
        prog = gem.apcaccess_pfad()
        log.info("apcaccess: %s", prog or "NICHT GEFUNDEN")

        if self.cfg.get("enabled", "1") != "1":
            log.warning("Das Plugin ist ausgeschaltet. Im Reiter Einstellungen "
                        "einschalten und speichern.")

        if self.cfg.get("mqtt", "1") == "1":
            self.mqtt.start()
        else:
            log.info("MQTT ist ausgeschaltet")

        intervall = max(5, gem.zahl(self.cfg, "intervall", 30, int))
        vollmeldung_alle = max(intervall, gem.zahl(self.cfg, "aktualisierung", 300, int))
        letzte_vollmeldung = 0

        while self.laeuft:
            if self.cfg.get("enabled", "1") == "1":
                erzwingen = (time.time() - letzte_vollmeldung) >= vollmeldung_alle
                self.durchgang(erzwingen=erzwingen)
                if erzwingen:
                    letzte_vollmeldung = time.time()

            if self._mtime() != self.config_mtime:
                log.info("Konfiguration geändert - wird neu eingelesen")
                self.config_mtime = self._mtime()
                self.cfg, _ = gem.konfiguration_lesen()
                self.letzter_stand.clear()
                intervall = max(5, gem.zahl(self.cfg, "intervall", 30, int))
                vollmeldung_alle = max(intervall,
                                       gem.zahl(self.cfg, "aktualisierung", 300, int))

            ende = time.time() + intervall
            while self.laeuft and time.time() < ende:
                time.sleep(min(1.0, max(0.05, ende - time.time())))

    def stop(self):
        self.laeuft = False
        self.mqtt.stop()


def main():
    dienst = Dienst()

    def beenden(signum, rahmen):   # noqa: ARG001
        log.info("Signal %s empfangen - beende", signum)
        dienst.laeuft = False

    signal.signal(signal.SIGTERM, beenden)
    signal.signal(signal.SIGINT, beenden)

    try:
        dienst.start()
    except KeyboardInterrupt:
        pass
    finally:
        dienst.stop()
        log.info("Beendet")


if __name__ == "__main__":
    main()
