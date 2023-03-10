function getDeps(){
    echo "$(apt show ${1} 2>/dev/null  | grep -P "Depends: " | sed 's~Depends:~~g;s~(~~g;s~)~~g;s~>~~g;s~<~~g' |tr -d " \t\n\r" | tr "," "\n")"
}
aptStr=$(dpkg-deb -I $(pwd)/${EXTENTION_DEB} | grep -P "Depends: " | sed 's~Depends:~~g;s~(~~g;s~)~~g;s~>~~g;s~<~~g' | tr -d " \t\n\r" | tr "," "\n")
plenumStr="$(getDeps $(echo "$aptStr" | grep plenum))"

echo -e "${aptStr} ${plenumstr}" | awk '!a[$0]++' > /tmp/aptStr