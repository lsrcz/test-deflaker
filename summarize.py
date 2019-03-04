#!/usr/local/bin/python3

def main():
    rerun = set()
    rerunCount = 0
    deflaker = set()
    deflakerCount = 0

    try:
        while True:
            line = input()
            testName = line.split()[3]
            if line.find('JVM') != -1:
                rerun.add(testName)
                rerunCount += 1
            else:
                deflaker.add(testName)
                deflakerCount += 1
    except EOFError as e:
        pass

    print('--- Summary ---')
    print('--- Rerun ---')
    print('Total:', rerunCount)
    print('Distinct:', len(rerun))
    print('Distinct flaky tests detected:')
    for s in rerun:
        print(s)
    print('--- DeFlaker ---')
    print('Count:', deflakerCount)
    print('Distinct:', len(deflaker))
    print('Distinct flaky tests detected:')
    for s in deflaker:
        print(s)

if __name__ == '__main__':
    main()

