while getopts "t:f:d:s:" opt; do
  case "$opt" in
      t) timeout=$OPTARG ;;
      f) file=$OPTARG ;;
      d) diff=$OPTARG ;;
      s) expSize=$OPTARG ;;
  esac
done
shift $((OPTIND-1))


start_watchdog(){
    timeout="$1"
    file="$2"
    diff="$3"
    expSize="$4"
    prevSize=0
    newSize=0
    SERVICE='xrdcp'
    user=$(whoami)
    while (( newSize<expSize ))
    do 
        sleep $timeout #check status after every x seconds
        if [ -e $file ]; then
            newSize=$(du -b $file | cut -f1)
            nextSize=$((prevSize+diff))
            wantSize=$((nextSize<expSize?nextSize:expSize))
            if [ $newSize -eq $expSize ]; then
                #finished
                exit 0
            fi
            if [ $newSize -lt $wantSize ]; then #if time out
                echo "killing process after timeout of $timeout seconds"
                if ps ax -u $user | grep -v grep | grep $SERVICE > /dev/null
                then
                    #xrdcp running, kill xrdcp now
                    pgrep -u $user xrdcp | xargs kill -9
                    exit 1
                else
                    #xrdcp already aborted on its own, use xrdcp exit code
                    xrdcp_abort=$?
                    exit $xrdcp_abort
                fi
                
            else #if file increases accordingly
                prevSize=$(du -b $file | cut -f1)
            fi
        else
            #file does not exist (timeout)
            if ps ax -u $user | grep -v grep | grep $SERVICE > /dev/null
            then
                #xrdcp running, killing now
                pgrep -u $user xrdcp | xargs kill -9
                exit 1
            else
               #xrdcp not running, use xrdcp exit code
                xrdcp_abort=$?
                exit $xrdcp_abort
            fi
        
        fi
    done
    
    
}

start_watchdog "$timeout" "$file" "$diff" "$expSize" &
watchdog_pid=$!
"$@"
cp_exit=$?
# If the cp command exits, kill the watchdog
kill $watchdog_pid
exit $cp_exit
