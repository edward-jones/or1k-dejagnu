#!/usr/bin/env python2


import sys
import re


if len(sys.argv) < 2:
    print >> sys.stderr, "Error: No test manifest provided"
    exit(-1)

# read in the test manifest
test_manifest = open(sys.argv[1], 'r')


# constants defining the possible results returned when a test is queried
# against the manifest.
ABSENT      = 'ABSENT'
PASS        = 'PASS'
XFAIL       = 'XFAIL'
UNSUPPORTED = 'UNSUPPORTED' 

# type of tests that may appear in a query or in the manifest
COMPILE_TEST      = 0
EXECUTE_TEST      = 1
TEST_FOR_WARNINGS = 2
TEST_FOR_ERRORS   = 3
TEST_FOR_BOGUS    = 4


# A test defined for line 0 actually means it may occur on any line
ANY_LINE = 0


# A dictionary to hold tests and their validity, read in from the manifest
# Test validity can be defined at the file level, or for individual
# combinations of flags and subtests.
test_dict = {}

# Regular expression to match entries in the manifest
test_regexp = re.compile(r'(PASS:|XFAIL:|UNSUPPORTED:) *(\S*) *([^\(]*)(\(test for ([\s\S]*), line ([0-9]*)\))?')


# parse tests from the manifest
for line in test_manifest:
    result = re.match(test_regexp, line)

    # ignore lines which don't match
    if not result:
        continue

    # extract the test details
    test_type = {
        'PASS:'       : PASS,
        'XFAIL:'      : XFAIL,
        'UNSUPPORTED:': UNSUPPORTED
    }[result.group(1)]
    test_file, flags_str, subtest, test_line = result.group(2, 3, 5, 6)

    # remove description field from the flags and turn into a tuple
    flags = filter(lambda x: x[0] == '-', filter(None, flags_str.split()))
    flags = tuple(flags)

    # check in the flag string to see if its an execution test
    if 'execution test' in flags_str:
        subtest = EXECUTE_TEST
    else:
        # not an execution test, get the type of subtest
        subtest = {
            None            : COMPILE_TEST,
            'warnings'      : TEST_FOR_WARNINGS,
            'errors'        : TEST_FOR_ERRORS,
            'bogus messages': TEST_FOR_BOGUS
        }[subtest]
    
    # if its a subtest, check whether it is for a specific line
    if (subtest != COMPILE_TEST) and (subtest != EXECUTE_TEST):
        if test_line:
            test_line = int(test_line)
    else:
        test_line = ANY_LINE

    # only add to the test dictionary if there isn't already an entry
    new_test = (test_file, flags, subtest, test_line)
    #if test_dict.get(new_test, None):
    #    print "Error: Manifest contains two entries for ", new_test
    #    exit(-1)
    test_dict[new_test] = test_type

print "READY"

while True:
    line = sys.stdin.readline()
    if not line:
        break

    args = line.split()

    # Get the test that is being run
    test_file = args[0]
   
    # Retrieve flags, subtest type and the subtest line
    flags = tuple(args[1:-2])
    subtest = {
        'COMPILE' : COMPILE_TEST,
        'EXECUTE' : EXECUTE_TEST,
        'WARNING' : TEST_FOR_WARNINGS,
        'ERROR'   : TEST_FOR_ERRORS,
        'BOGUS'   : TEST_FOR_BOGUS
    }[args[-2]]
    test_line = int(args[-1])

    # Check if there is an entry for this specific test
    if subtest != COMPILE_TEST and flags != () and test_line != 0:
        result = test_dict.get((test_file, flags, subtest, test_line), None)
        if result is not None:
            print result
            continue

    # This specific subtest on any line
    if subtest != COMPILE_TEST and flags != ():
        result = test_dict.get((test_file, flags, subtest, 0), None)
        if result is not None:
            print result
            continue

    # This specfic subtest with any flags
    if subtest != COMPILE_TEST and test_line != 0:
        result = test_dict.get((test_file, (), subtest, test_line), None)
        if result is not None:
            print result
            continue

    # On any line with any flags
    if subtest != COMPILE_TEST:
        result = test_dict.get((test_file, (), subtest, 0), None)
        if result is not None:
            print result
            continue

    # Any entry with these flags
    if flags != ():
        result = test_dict.get((test_file, flags, COMPILE_TEST, 0), None)
        if result is not None:
            print result
            continue

    # Any entry with any flags
    result = test_dict.get((test_file, (), COMPILE_TEST, 0), None)
    if result is not None:
        print result
        continue

    # No entry for this file
    print ABSENT

