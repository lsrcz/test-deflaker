#!/usr/bin/env python3

import os
import re

topLineRe = re.compile(r'\[INFO\] \-\-\- (?P<plugin>[a-z\-]+):(?P<version>[0-9\.]+):(?P<phase>[a-z\-]+) \((?P<name>[a-z\-]+)\) @ (?P<module>[a-z\-]+) \-\-\-')
summaryRe = re.compile(r'Tests run: [0-9]+, Failures: (?P<failure>[0-9]+), Errors: (?P<error>[0-9]+), Skipped: [0-9]+(, Flakes: (?P<flakes>[0-9]+))?')
nameRe = re.compile(r'(?P<name>[\w\.]+)\((?P<suite>[\w\.]+)\)')
flakyRe = re.compile(r'\[WARNING\] FLAKY>> Test (?P<name>[\w\.]+) failed, but did not appear to run any changed code')
flakyRerunRe = re.compile(r'\[WARNING\] FLAKY>> Test (?P<name>[\w\.]+) was found to be flaky by rerunning it in')
interestingName = ['default-test', 'default-test-rerunfailures', 'deflaker-report-tests']

def analyzeResult(l):
    resultType = 'failure'
    failureCnt = 0
    flakyCnt = 0
    ret = {'failure': set(), 'flaky': set()}
    for line in l:
        m = re.match(summaryRe, line)
        if m is not None:
            failureCnt = int(m.group('failure')) + int(m.group('error'))
            if m.group('flakes') is not None:
                flakyCnt = int(m.group('flakes'))
            assert len(ret['failure']) == failureCnt + flakyCnt
            assert len(ret['flaky']) == flakyCnt
            break
        if line.startswith('Failed tests:') or line.startswith('Tests in error:'):
            resultType = 'failure'
        if line.startswith('Flaked tests:'):
            resultType = 'flaky'
        m1 = re.match(nameRe, line)
        if m1 is not None:
            ret['failure'].add(m1.group('name'))
            ret[resultType].add(m1.group('name'))
    return ret

def analyzeDeFlaker(l):
    ret = {'DeFlaker': set(), 'Rerun': set()}
    for line in l:
        m = re.match(flakyRe, line)
        if m is not None:
            ret['DeFlaker'].add(m.group('name'))
        m = re.match(flakyRerunRe, line)
        if m is not None:
            ret['Rerun'].add(m.group('name'))
    if len(ret['DeFlaker']) < len(ret['Rerun']):
        print(ret)
    return ret

def analyze(d):
    preprocessed = dict(map(lambda x: (x[0],
                                       {'default-test': analyzeResult(x[1]['default-test']),
                                        'default-test-rerunfailures': analyzeResult(x[1]['default-test-rerunfailures']),
                                        'deflaker-report-tests': analyzeDeFlaker(x[1]['deflaker-report-tests'])
                                        }
                                       ), d.items()))
    allFailures = set()
    allRerun = set()
    allDeFlaker = set()
    for module in preprocessed:
        dt = preprocessed[module]['default-test']
        dtr = preprocessed[module]['default-test-rerunfailures']
        df = preprocessed[module]['deflaker-report-tests']
        allFailures |= dt['failure']
        flakySet = dt['flaky'] | dtr['flaky'] # | (dt['failure'] - dtr['failure'])
        allRerun |= flakySet
        assert flakySet == df['Rerun']
        allDeFlaker |= df['DeFlaker']

    return allFailures, allRerun, allDeFlaker

def splitFile(f):
    name = ''
    module = ''
    stack = []
    ret = {}
    resultsSeen = False
    for line in f:
        m = re.match(topLineRe, line)
        if m is not None:
            if name in interestingName:
                if module not in ret:
                    ret[module] = {}
                ret[module][name] = stack
            name = m.group('name')
            module = m.group('module')
            resultsSeen = False
            stack = []
        if name in interestingName:
            if line.startswith('Results :'):
                resultsSeen = True
            if name.startswith('deflaker') or resultsSeen:
                stack.append(line)
    return ret


def analyzeFile(filename):
    with open(filename) as f:
        splitted = splitFile(f)
        return analyze(splitted)



def main():
    t = list(map(lambda x: os.path.join('logs', x),
                 filter(lambda x: x.startswith('failed'),
                        os.listdir('logs'))))
    totCnt = 0
    rerunCnt = 0
    deflakerCnt = 0
    for l in t:
        print(l)
        tot, rerun, deflaker = analyzeFile(l)
        totFormer, rerunFormer, deflakerFormer = analyzeFile(l.replace('failed', 'former'))
        tot = tot - totFormer
        rerun &= tot
        deflaker &= tot
        totCnt += len(tot)
        rerunCnt += len(rerun)
        deflakerCnt += len(deflaker)
    print(totCnt, rerunCnt, deflakerCnt)

if __name__ == '__main__':
    main()
