#!/bin/bash

cd ninja

setrepo() {
    git reset $1
    git clean -fd
    git checkout -- .
    sed -i "" "/\/pluginManage/a\\
    <extensions>\\
    <extension>\\
    <groupId>org.deflaker</groupId>\\
    <artifactId>deflaker-maven-extension</artifactId>\\
    <version>1.4</version>\\
    </extension>\\
    </extensions>\\
    " pom.xml
}

setrepo $1
mvn clean
mvn install
mvn clean
mvn verify 2>&1 > $1.log
if (grep 'There are test failures' $1.log)
then
    mv $1.log ../logs/failed-$1.log
    setrepo "$1^"
    mvn clean
    mvn install
    mvn clean
    mvn verify 2>&1 > $1.log
    mv $1.log ../logs/former-$1.log
else
    mv $1.log ../logs/ok-$1.log
fi

