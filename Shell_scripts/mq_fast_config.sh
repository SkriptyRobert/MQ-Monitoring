#!/bin/bash

# Configuration settings - adjust these values as needed
QMGR="QM3"               # Queue Manager name
CHANNEL="QM3.SVRCONN"    # Server connection channel name
LISTENER="LISTENER.QM3"  # Listener name
PORT="1416"              # Port number for the listener
USER="pesourob"           # User for MQ authorization

# Check if the Queue Manager is already running
echo "Checking if Queue Manager $QMGR is running..."
QM_STATUS=$(dspmq | grep "$QMGR" | awk '{print $3}')
if [ "$QM_STATUS" != "Running" ]; then
  echo "Queue Manager $QMGR is not running. Starting it now."
  strmqm $QMGR
else
  echo "Queue Manager $QMGR is already running."
fi

# Remove existing channel if it exists
echo "Deleting existing channel $CHANNEL if it exists."
echo "DELETE CHANNEL($CHANNEL)" | runmqsc $QMGR

# Remove existing authorization record for the user
echo "Deleting existing AUTHREC for user $USER."
echo "DELETE AUTHREC PROFILE('$CHANNEL') OBJTYPE(CHANNEL) PRINCIPAL('$USER')" | runmqsc $QMGR

# Remove existing CHLAUTH for the channel
echo "Deleting existing CHLAUTH rule for channel $CHANNEL."
echo "DELETE CHLAUTH('$CHANNEL')" | runmqsc $QMGR

# Remove the listener if it already exists
echo "Deleting existing listener $LISTENER if it exists."
echo "DELETE LISTENER($LISTENER)" | runmqsc $QMGR

# Create a new listener on the specified port
echo "Creating listener on port $PORT."
echo "DEFINE LISTENER($LISTENER) TRPTYPE(TCP) PORT($PORT) CONTROL(QMGR) REPLACE" | runmqsc $QMGR
echo "START LISTENER($LISTENER)" | runmqsc $QMGR

# Create the channel for server connection
echo "Creating channel $CHANNEL."
echo "DEFINE CHANNEL($CHANNEL) CHLTYPE(SVRCONN) REPLACE" | runmqsc $QMGR

# Configure authentication for the channel
echo "Configuring authentication for channel $CHANNEL."
echo "SET CHLAUTH('$CHANNEL') TYPE(ADDRESSMAP) ADDRESS('*') USERSRC(NOACCESS) ACTION(REMOVE)" | runmqsc $QMGR
echo "SET CHLAUTH('$CHANNEL') TYPE(USERMAP) CLNTUSER('$USER') USERSRC(CHANNEL) ACTION(ADD)" | runmqsc $QMGR

# Disable Queue Manager-level authentication if needed
echo "Disabling Queue Manager authentication if required."
echo "ALTER QMGR CONNAUTH('')" | runmqsc $QMGR

# Grant necessary permissions to the user
echo "Granting permissions to user $USER."
setmqaut -m $QMGR -t q -n "QM2.*" -p $USER +all
setmqaut -m $QMGR -t q -n "$CHANNEL" -p $USER +put +inq +connect
setmqaut -m $QMGR -t qmgr -p $USER +connect
setmqaut -m $QMGR -t q -n "QM2.*" -p $USER +all

# Restart the Queue Manager to apply changes
echo "Restarting Queue Manager $QMGR to apply changes."
endmqm $QMGR
strmqm $QMGR

echo "Configuration for Queue Manager $QMGR, channel $CHANNEL, and listener $LISTENER on port $PORT completed successfully."
