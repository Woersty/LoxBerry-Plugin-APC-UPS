#!/bin/sh

# To use important variables from command line use the following code:
COMMAND=$0    # Zero argument is shell command
PTEMPDIR=$1   # First argument is temp folder during install
PSHNAME=$2    # Second argument is Plugin-Name for scipts etc.
PDIR=$3       # Third argument is Plugin installation folder
PVERSION=$4   # Forth argument is Plugin version
#LBHOMEDIR=$5 # Comes from /etc/environment now.

PCGI=$LBPCGI/$PDIR
PHTML=$LBPHTML/$PDIR
PTEMPL=$LBPTEMPL/$PDIR
PDATA=$LBPDATA/$PDIR
PLOG=$LBPLOG/$PDIR
PCONFIG=$LBPCONFIG/$PDIR
PSBIN=$LBPSBIN/$PDIR
PBIN=$LBPBIN/$PDIR

echo "<INFO> Copy back existing config files"
cp -v -r /tmp/${PDIR}.SAVE/* $PCONFIG/ 2>/dev/null
rm -rf /tmp/${PDIR}.SAVE

# --- APC-UPS --------------------------------------------------------------
chmod 755 "$LBPBIN/$PDIR"/*.py 2>/dev/null

# apcupsd muss laufen, sonst antwortet apcaccess nicht.
if command -v systemctl >/dev/null 2>&1; then
    systemctl enable apcupsd >/dev/null 2>&1
    systemctl start  apcupsd >/dev/null 2>&1
fi

# ISCONFIGURED steht bei Debian nach der Installation auf "no" - solange
# startet apcupsd nicht. Das ist die einzige Systemdatei, die dieses Plugin
# anfasst, und sie muss angefasst werden.
if [ -f /etc/default/apcupsd ]; then
    if grep -q "^ISCONFIGURED=no" /etc/default/apcupsd; then
        sed -i "s/^ISCONFIGURED=no/ISCONFIGURED=yes/" /etc/default/apcupsd
        echo "<INFO> ISCONFIGURED in /etc/default/apcupsd auf yes gesetzt."
        systemctl restart apcupsd >/dev/null 2>&1
    else
        echo "<OK> /etc/default/apcupsd ist bereits eingerichtet."
    fi
fi

# Pruefen, ob die Bausteine da sind.
if command -v apcaccess >/dev/null 2>&1; then
    echo "<OK> apcaccess gefunden: $(command -v apcaccess)"
else
    echo "<WARNING> apcaccess fehlt. Nachinstallieren: sudo apt-get install -y apcupsd"
fi
if python3 -c "import paho.mqtt.client" >/dev/null 2>&1; then
    echo "<OK> Python-Modul paho.mqtt vorhanden."
else
    echo "<WARNING> paho-mqtt fehlt. Nachinstallieren: sudo apt-get install -y python3-paho-mqtt"
fi
if apcaccess status >/dev/null 2>&1; then
    echo "<OK> Die USV antwortet."
else
    echo "<INFO> Die USV antwortet noch nicht. Ist sie per USB angeschlossen?"
    echo "<INFO> Der Reiter Test zeigt, woran es liegt."
fi

echo "<INFO> Naechster Schritt: Reiter Test -> Jetzt abfragen."

exit 0
