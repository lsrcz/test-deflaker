# test-deflaker

## Generating the data
I selected the first 260 commits of ninja with the [ninja.sh](ninja.sh) script
```bash
# awk -F"\"" '{ if($2 == "ninja") print $4}' historical_project_versions.csv | xargs -t -n 1 -I{} ./ninjarun-old.sh {}
awk -F"\"" '{ if($2 == "ninja") print $4}' historical_project_versions.csv | xargs -t -n 1 -I{} ./ninjarun.sh {}
```

The data in [logs-old](logs-old) was generated by running a script similar to [ninjarun-old.sh](ninjarun-old.sh), and the data in [logs](logs) was generated by running [ninja.sh](ninja.sh) with [ninjarun.sh](ninjarun.sh).

The difference between [ninjarun-old.sh](ninjarun-old.sh) and [ninjarun.sh](ninjarun.sh) is that the old script won't do `mvn clean` before `mvn verify`, and it won't build the previous commits for the failed commits.

For your convenience, here is the code for [ninjarun.sh](ninjarun.sh):
```bash
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
```

The data is generated on macOS 10.14.4 Beta(18E194d) with maven 3.3.9 and Oracle JDK 1.8.0_162. The running time is about 17 hrs.

## Analyzing the data
If we consider all test failures, including those who fails both on the previous commits and the current commits:

For the old data,
```bash
grep 'FLAKY' logs-old/failed-* | python3 summarize.py
```
gives
```text
--- Summary ---
--- Rerun ---
Total: 59
Distinct: 1
Distinct flaky tests detected:
controllers.ApplicationControllerTest.testThatHomepageWorks
--- DeFlaker ---
Count: 165
Distinct: 9
Distinct flaky tests detected:
example.ExampleIntegrationTest.testIndexRoute
conf.RoutesTest.testReverseRoutingWithArrayAndQueryParameters
example.ExampleIntegrationTest.testThatInvalidStaticAssetsAreNotFound
controllers.ApplicationControllerFluentLeniumTest.testThatHomepageWorks
controllers.ApiControllerDocTesterTest.testGetAndPostArticleViaJson
example.ExampleIntegrationTest.testThatStaticAssetsWork
conf.RoutesTest.testReverseRoutingWithMapAndQueryParameter
controllers.ApiControllerDocTest.testGetAndPostArticleViaJson
controllers.ApplicationControllerTest.testThatHomepageWorks
```

For the new data,
```bash
grep 'FLAKY' logs/failed-* | python3 summarize.py
```
gives
```text
--- Summary ---
--- Rerun ---
Total: 60
Distinct: 1
Distinct flaky tests detected:
controllers.ApplicationControllerTest.testThatHomepageWorks
--- DeFlaker ---
Count: 89
Distinct: 5
Distinct flaky tests detected:
controllers.ApplicationControllerTest.testThatHomepageWorks
conf.RoutesTest.testReverseRoutingWithMapAndQueryParameter
controllers.ApiControllerDocTesterTest.testGetAndPostArticleViaJson
controllers.ApiControllerDocTest.testGetAndPostArticleViaJson
conf.RoutesTest.testReverseRoutingWithArrayAndQueryParameters
```

Compared to the old data, DeFlaker detected less flaky tests in the new data. And notice that 4 tests are no longer detected.
```bash
$ grep 'FLAKY' logs-old/failed-* | grep -E "FluentLenium|example" | wc
     69    1064   14452
```

If only consider the new test failures, here is the result:
```bash
$ python3 analyze.py
... (irrelevant lines)
('Total failure: ', 66)
('Rerun: ', 47)
('DeFlaker: ', 38)
```

It seems that Rerun detects more flaky tests in this scenerio(although they are all the same test case `controllers.ApplicationControllerTest.testThatHomepageWorks`).

## Limitations
Maybe Ninja is not a good example here? I chose to test on it just because I didn't have enough computational power, and the test suite of ninja is relatively small, so I can evaluate DeFlaker on more commits.

## The questions
1. Why are the results of the two scripts so different? The only related difference of the two scripts is the `mvn clean`. Maybe ninja is not a good example here? Perhaps the reason for this phenomenon is that ninja's test suite depends on some external state and `mvn clean` clears it.
2. What's the default strategy of the current implementation? I found that all flaky tests detected by rerun are reported as
   > "FLAKY>> Test " + testKey + " was found to be flaky by rerunning it in the same JVM! It failed the first time, then eventually passed."
   
   Will the `default-test-rerunfailures` phase rerun the tests in a new JVM? If so, why don't DeFlaker report something like "by rerunning it in the fresh JVM"?
   
   If not, it seems that the current implementation reruns each test for 10 times in the same JVM, although they are divided into two groups.
3. Do I misunderstand the meaning of a "previous commit"? Is it the previous commit in the git repo or the previous commit in the csv file?

## Minor bugs of DeFlaker
1. DeFlaker won't work with maven 3.6.0. [Issue](https://github.com/gmu-swe/deflaker/issues/3).
2. DeFlaker may break the intellij IDEA's unit test functionalities. [Issue](https://github.com/gmu-swe/deflaker/issues/4).
