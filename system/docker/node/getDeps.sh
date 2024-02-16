MAX_DEPENDANCY_DEPTH=${MAX_DEPENDANCY_DEPTH:-2}

function getDebDependencies(){
    echo "$(dpkg-deb -I ${1} | grep -P "Depends: " | sed 's~Depends:~~g;s~(~~g;s~)~~g;s~>~~g;s~<~~g' | tr -d " \t\n\r" | tr "," "\n")"
}

function getPackageDependencies(){
    echo "$(apt show ${1} 2>/dev/null  | grep -P "Depends: " | sed 's~Depends:~~g;s~(~~g;s~)~~g;s~>~~g;s~<~~g' |tr -d " \t\n\r" | tr "," "\n")"
}

function buildAptStr(){
    dependancyList=${1}
    local level=${2:-1}
    # Limit recursion
    if (( ${MAX_DEPENDANCY_DEPTH} > 0 && ${level} > ${MAX_DEPENDANCY_DEPTH} )); then
        return
    fi

    for dependancy in ${dependancyList}; do
        if (( ${level} == 1 )); then
            echo "  - ${dependancy} (top)"
            aptStr+="${dependancy}\n"
        fi

        if (( ${MAX_DEPENDANCY_DEPTH} > 0 )); then
            packageList=$(getPackageDependencies ${dependancy})
            if [ ! -z "${packageList}" ]; then
                for package in ${packageList}; do
                    padding=$(expr 4 \* ${level})
                    printf "%-${padding}s- " " "
                    printf "${package} (level ${level})"
                    printf "\n"

                    aptStr+="${package}\n"
                    buildAptStr "${package}" "$(expr ${level} + 1)"
                done
            fi
        fi
    done
}

function getDependencies(){
  debDependencies=$(getDebDependencies ${debPackage})
  buildAptStr "${debDependencies}"
}

# =============================================================================================================================================
# Main Script
# Set MAX_DEPENDANCY_DEPTH=0 to get the just the top level dependancies for the ded package.
# ---------------------------------------------------------------------------------------------------------------------------------------------
debPackage=${1}
echo -e "\n${debPackage} contains the following dependancies (traversed ${MAX_DEPENDANCY_DEPTH} levels):"
getDependencies "${debPackage}"
echo
echo -e "${aptStr}" | awk '!a[$0]++' > /tmp/aptStr
# =============================================================================================================================================
