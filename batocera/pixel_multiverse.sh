#!/bin/sh
#
# pixel-multiverse - init.d script for Batocera

PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="pixel_multiverse"
NAME=service.py
DAEMON=/userdata/pixel_multiverse/service.py
PIDFILE=/run/pixel_multiverse.pid
LOG_FILE=/userdata/system/logs/pixel_multiverse.log

# Exit if the package is not installed
[ -x "$DAEMON" ] || exit 0

# Function that starts the daemon/service
do_start() {
    printf "Starting $DESC: $NAME "

    start-stop-daemon --start --background --make-pidfile --pidfile "${PIDFILE}" --output "${LOG_FILE}" --exec ${DAEMON} \
        && echo "OK" || echo "FAIL"
}

# Function that stops the daemon/service
do_stop() {
    printf "Stopping $DESC: $NAME "
    start-stop-daemon --stop --remove-pidfile --pidfile "${PIDFILE}" --name "${NAME}" \
        && echo "OK" || echo "FAIL"
}

do_status() {
    printf "Status of $DESC: $NAME "
    start-stop-daemon --status --pidfile "${PIDFILE}" --name "${NAME}" \
        && echo "OK" || echo "FAIL"
}

case "$1" in
    start)
        do_start
        RETVAL=$?
        ;;
    status)
        do_status
        RETVAL=$?
        ;;
    stop)
        do_stop
        RETVAL=$?
        ;;
    restart|force-reload)
        do_stop
        sleep 1
        do_start
        RETVAL=$?
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|force-reload}" >&2
        RETVAL=3
        ;;
esac

exit $RETVAL
