#!/usr/bin/env python3

import sys
import os
import argparse
import logging
import datetime
import dateutil
import time
import tempfile
import subprocess
import atexit
import shutil
import json
import socket

# TODO: add the following to the install/config README:
#
# Setup aws configuration
# Create ~/.aws/credentials
#[default]
#aws_access_key_id = YOUR_ACCESS_KEY
#aws_secret_access_key = YOUR_SECRET_KEY
# Create ~/.aws/config
#[default]
#region=us-west-2
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
import boto3

from io import StringIO

logger = logging.getLogger(__name__)

# Command-line Argument Parsing
def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(
            'Boolean value (yes, no, true, false, y, n, 1, or 0) expected.')


LOG_LEVEL_HELP = """Logging level.
                      [LOG-LEVEL]: notset, debug, info, warning, error, critical
                      Default: info"""
levels = {
    'notset': logging.NOTSET,
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def log_level(v):
    if v.lower() in levels.keys():
        return levels[v.lower()]
    else:
        raise argparse.ArgumentTypeError(
            'Expected one of the following: {}.'.format(
                 ', '.join(levels.keys())))

def experiment_dict(v):
    common_msg = "Invalid experiment run configuration."
    experiments = {}
    try:
        edict = json.loads(v)
    except Exception as e:
        raise argparse.ArgumentTypeError('{} Reason: {}'.format(common_msg, e))

    # Validate each of the directories in the path
    if "path" in edict:
        invalid_experiment_dirs = []

        for experiment_dir in edict['path']:
           # Does the directory contain a 'scripts' directory?
           if not os.path.exists("{}/scripts".format(experiment_dir)):
               invalid_experiment_dirs.append(experiment_dir)

        if invalid_experiment_dirs:
            message = "Invalid 'path' element. The following directories do " \
                      "not contain a 'scripts' sub-directory: {}".format(
                      invalid_experiment_dirs)
            # Fail false if path(s) are invalid. Experiment discovery/validation
            # should not continue if there is one or more invalid directories in
            # the 'path' list/element.
            raise argparse.ArgumentTypeError(message)

    validation_errors = []

    # Validate if the enumerated experiment(s) exist
    de = default_experiments(path=edict.get("path", None))
    invalid_experiments = []
    if "experiments" in edict:
        experiments = edict['experiments']
        for experiment in experiments:
            if experiment not in de:
                invalid_experiments.append(experiment)
            else:
                # Ensure the run_script is defined in each experiment.
                # IMPORTANT: "run_script" is a reserved word/key in each
                #            experiment. "run_script" cannot be a parameter to
                #            an experiment's run-<experiment name> bash script.
                #            The "run_script" key/value pair will be stripped
                #            out of each experiment before all other key/value
                #            pairs are processed and passed to the experiment's
                #            run-<experiment name> bash script.
                run_script = de[experiment]['run_script']
                experiments[experiment]['run_script'] = run_script
    else:
        experiments = de

    if invalid_experiments:
        message = "Invalid 'experiments' element. The following experiments " \
                  "do not exist: {}".format(invalid_experiments)
        validation_errors.append(message)

    # Validate each of the excluded experiments
    if "exclude" in edict:
        invalid_experiments = []
        for experiment in edict['exclude']:
            if experiment not in de:
                 invalid_experiments.append(experiment)
            elif experiment in experiments:
                 del experiments[experiment]
                 logger.debug("Removed %s from the set of experiments to " \
                              "run...", experiment)

        if invalid_experiments:
            message = "Invalid 'exclude' element. The following experiments " \
                      "do not exist: {}".format(invalid_experiments)
            validation_errors.append(message)

    if validation_errors:
        message = ""
        for error in validation_errors:
            if message:
                message += " "
            message += error
        raise argparse.ArgumentTypeError(message)
    return experiments

def program_args(parser=None):
    if not parser:
        parser = argparse.ArgumentParser()

    parser.add_argument('pool', help='The pool against which to run the ' \
                        'experiment(s). A directory with this name must exist' \
                        ' in the user\'s home directory that contains the ' \
                        ' following files (or at least symlinks to them):' \
                        ' 1. \'pool_transactions_genesis\'' \
                        ' 2. \'clients\' - Comma separated list of clients.' \
                        ' 3. \'ssh_config\' - One entry for each client and' \
                        ' node. See \'man ssh_config\' for details.' \
                        ' 4. PEM file(s). Use the optional pool-config-dir ' \
                        'argument if the directory containing these files is ' \
                        'located elsewhere on the client.')

    parser.add_argument('--job-id', help='The job ID. This will typically be ' \
                        'the Jenkins \'BUILD_TAG\'.', default=None)

    parser.add_argument('--pool-config-dir', help='The location of the ' \
                        'directory on the client that contains pool ' \
                        'configuration files. See \'pool\' argument help for ' \
                        'details. Default: user\'s home directory.',
                        default='~')

    parser.add_argument('--s3bucket', help='The name of the S3 bucket in ' \
                        ' which to store experiment output (succeed or fail).'\
                        ' At minimum, the client designated by the \'client\' '\
                        'argument must be configured to upload files to S3. ' \
                        'Default: None', nargs='?', const=None, default=None)

    #run_script_dir = os.path.dirname(os.path.realpath(__file__))
    #parser.add_argument('--experiment-path', type=experiment_path, help='A ' \
                        #'comma separated list of directories in which to ' \
                        #'search for experiments. Each directory must have a ' \
                        #'"scripts" subdirectory that contains one or more ' \
                        #'run-* scripts. Default: {}'.format(run_script_dir),
                        #default=run_script_dir)

    parser.add_argument('--experiments', type=experiment_dict, help='A JSON ' \
                        'document/string enumerating the experiments to run ' \
                        'and the parameters to pass to each experiment. ' \
                        'Example 1: Omitting this option results in all ' \
                        'chaosindy experiments running with their default ' \
                        'parameters. Example 2: Run the run-force-view-change' \
                        ' script and override the default execution-count (1)' \
                        ' and write-nym-timeout (60 seconds): --experiments=' \
                        '\'{"experiments": {"force-view-change": ' \
                        '{"execution-count" : "10", "write-nym-timeout": "20"}}}\'' \
                        ' See the -h output for each scripts/run-* script for' \
                        ' possible parameters. Example 3: Run all run-* ' \
                        ' scripts found in ./scripts and /foo/scripts, ' \
                        'excluding the force-view-change experiment: ' \
                        '--experiments=\'{"path": ["./", "/foo"], "exclude": ' \
                        '["force-view-change"]}\' '
                        'Default: None', default=None)

    parser.add_argument('-c', '--cleanup', type=str2bool, help='Each call to ' \
                        'this script creates a temporary directory. Each ' \
                        'experiment executed by this script creates a ' \
                        'directory in the temporary directory. Each ' \
                        'experiment\'s directory will contain the results of ' \
                        'the experiment. These results are uploaded to an S3 ' \
                        'bucket if the bucket name is provided (see ' \
                        '--s3bucket argument). Should this temporary ' \
                        'directory be deleted when this script exits? ' \
                        'Default: Y Options (case insensitive): y, yes, true,' \
                        ' 1, n, no, false, 0', nargs='?', const='Y',
                        default='Y')

    parser.add_argument('-t', '--test', action='store_true',
                        default=False, help='Runs unit tests and exits.')

    parser.add_argument('-l', '--log-level', type=log_level, nargs='?',
                        const=logging.INFO, default=logging.INFO,
                        help=LOG_LEVEL_HELP)

    return parser


def parse_args(argv=None, parser=program_args()):
    return parser.parse_args(args=argv)


# Clean up anything that is created by this script
def clean_up(job_dir):
    logger.info("Deleting job dir %s...", job_dir)


def init(args):
    # Log to stdout
    # TODO: decide if logging to stdout is permanent
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(args.log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.setLevel(args.log_level)
    logger.debug("Initializing...")
    logger.debug("args: %s", args)


def create_job_dir(build_tag):
    # Get ISO 8601 formatted datetime and create a job dirname
    job_dirname = "{}-{}".format(build_tag, datetime.datetime.now().isoformat())
    #job_dir_path = tempfile.TemporaryDirectory(prefix=job_dirname) 
    job_dir_path = tempfile.mkdtemp(prefix=job_dirname) 
    logger.debug("Temporary Job Dir: {}".format(job_dir_path))
    return job_dir_path


def get_scripts_dir(directory = None):
    if directory:
        scripts_dir = os.path.join(directory, "scripts")
    else:
        script_path = os.path.dirname(os.path.realpath(__file__))
        scripts_dir = os.path.join(script_path, "scripts")
    return scripts_dir


def reset_pool(pool):
    # TODO: Add functions to chaosindy repo/module to reset pool
    logger.debug("TODO: Resetting pool %s... NYI in run.py, but the feature " \
                 "exists in the chaosindy python module.", pool)


def capture_node_state(pool, job_dir):
    # TODO: Add functions to chaosindy repo/module to capture node state
    logger.debug("Capturing node state (nscapture archives) for pool %s and "\
                 "storing results in %s...", pool, job_dir)


def run_experiment(pool, job_dir, experiment, experiment_script, parameters):
    # Each experiment run by each job gets it's own directory.
    # Create experiment directory within the job_dir
    experiment_dir_path = os.path.join(job_dir, experiment)
    try:
        logger.info("Creating experiment directory " \
                     "{}".format(experiment_dir_path))
        os.mkdir(experiment_dir_path)
    except Exception as e:
        logger.error("Failed to create experiment " \
                     "directory {}".format(experiment_dir_path))
    logger.debug("Created directory {} for" \
                 " experiment {}".format(experiment_dir_path, experiment))
    logger.debug("Running experiment {} with parameters {} and placing " \
                 "results in {}".format(experiment_script, parameters.keys(),
                 job_dir))

    # Build arguments list
    arguments = [experiment_script]
    # Append pool/pool_transaction_genesis with --genesis-file
    arguments.append("--genesis-file")
    arguments.append(os.path.expanduser(os.path.join("~", pool, "pool_transactions_genesis")))
    # Append pool/ssh_config with --ssh-config-file
    arguments.append("--ssh-config-file")
    arguments.append(os.path.expanduser(os.path.join("~", pool, "ssh_config")))
    # Append pool/clients with --load-client-nodes
    clients = []
    with open(os.path.expanduser(os.path.join("~", pool, "clients")), 'r') as clients_file:
        clients = json.load(clients_file)
    arguments.append("--load-client-nodes")
    arguments.append(",".join(clients))
    # TODO: Perform some preflight configuration tests to ensure the given pool
    #       (directory containing pool_transactions_genesis, ssh_config, and
    #       clients files) is configured properly
    #       1. Make sure each alias defined in the pool_transactions_genesis has
    #          an entry in the ssh_config file.
    #       2. Make sure each alias defined in the clients file has an entry in
    #          the ssh_config file.
    #       3. Make sure each entry in the ssh_config file has the following
    #          format:
    #          Host <host>
    #              User <user>
    #              Hostname <IP>
    #              IdentityFile <path to PEM or private key file>
    #       4. Make sure each IdentityFile exists/resolves.
    for k, v in parameters.items():
        arguments.append("--{}".format(k))
        arguments.append(v)
    # Execute the experiment
    result = subprocess.run(arguments, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd=experiment_dir_path)

    # Check the experiment's return code
    status = "succeeded"
    try:
        result.check_returncode()
        # Experiment ran without failure.
        logger.debug("Chaos experiment %s succeeded.", experiment)
    except subprocess.CalledProcessError:
        # Experiment failed.
        logger.debug("Chaos experiment %s failed with a return code of %d.",
                     experiment, result.returncode)
        # Capture node state for each node in the pool
        capture_node_state(pool, job_dir)
        status = "failed"

    # Write the return code, stdout, and stderr to a "run.out" file in the
    # job_dir. It will be useful during the analyze step.
    result_stdout = result.stdout.decode('utf-8') if result.stdout else None
    result_stderr = result.stderr.decode('utf-8') if result.stderr else None
    result_dict = {
        'returncode': result.returncode,
        'stdout': result_stdout,
        'stderr': result_stderr
    }
    run_out_file = os.path.join(experiment_dir_path, "run.out")
    with open(run_out_file, 'w') as outfile:
        json.dump(result_dict, outfile)

    # Check the "run" list for activities that have an "output" that is not set
    # to true (or explicitly look for "output": false.
    journal_file = os.path.join(experiment_dir_path, "journal.json")
    failed_activities = []
    with open(journal_file, "r") as f:
        journal = json.load(f)
        for activity in journal['run']:
            if activity['output'] == False:
                failed_activities.append(activity['activity']['name'])
    if failed_activities:
        status += " but failed activities: {}".format(",".join(failed_activities))

    # Write an entry to the "report" file in the job_dir
    # TODO: Make the report more comprehensive. See run.py TODOs in the
    #       README.md file.
    report_file = os.path.join(job_dir, "report")
    with open(report_file, 'a') as report:
        report.write("{}: {}\n".format(experiment, status))

def discover_experiments(scripts_dir):
    experiments = {}
    for filename in os.listdir(scripts_dir):
        if filename[0:4] == "run-":
            experiment = filename[4:]
            # IMPORTANT: "run_script" is a reserved word/key in each experiment.
            #            "run_script" cannot be a parameter to an experiment's
            #            run-<experiment name> bash script. The "run_script"
            #            key/value pair will be stripped out of each experiment
            #            before all other key/value pairs are processed and
            #            passed to the experiment's run-<experiment name> bash
            #            script.
            experiments[experiment] = {
                "run_script": os.path.join(scripts_dir, filename)
            }
    return experiments

def default_experiments(path = None):
    logger.debug("Getting default experiments...")
    experiments = {}
    if path:
        for directory in path:
            new_experiments = discover_experiments(get_scripts_dir(directory))
            experiments.update(new_experiments)
    else:
        scripts_dir = get_scripts_dir()
        new_experiments = discover_experiments(scripts_dir)
        experiments.update(new_experiments)
    return experiments

def run_experiments(pool, job_dir, experiments={}):
    if not experiments:
        experiments = default_experiments()
        logger.debug("Using default set of experiments: %s",
                     ', '.join(list(experiments.keys())))

    # Run each experiment iff
    for experiment, parameters in experiments.items():
        parameters_msg = ""
        run_script = parameters['run_script']
        del parameters['run_script']
        parameters_list = ', '.join(list(parameters.keys()))
        if parameters_list:
            parameters_msg = " and overriding default " \
                               "parameters: {}".format(parameters_list)
        else:
            parameters_msg = " using default parameters"
        logger.info("Running experiment %s%s", experiment, parameters_msg)
        reset_pool(pool)
        run_experiment(pool, job_dir, experiment, run_script, parameters)


def upload(job_dir):
    # Upload results to S3
    pass


def notify(output_location):
    # TODO: notify interested parties (email, slack, etc.)
    logger.info("Chaos experiment results can be found in %s", output_location)


def process_results(job_dir, s3bucket):
    # TODO: Create Chaos experiments report. What experiments passed and failed
    #       and where is experiment output located?
    logger.debug("Processing experiment results located in {}".format(job_dir))

    # Upload results to S3?
    if s3bucket:
        upload(job_dir)
        notify("S3 Bucket: {}".format(s3bucket))
    else:
        notify("Temporary Job Directory: {}:{}".format(socket.gethostname(),
                                                       job_dir))



def main(args):
    try:
        init(args)
    except Exception:
        logger.error('Unable to initialize script')
        raise

    # Create a <JENKINS BUILD_TAG>-<ISO 8601 datetime> folder in the S3 bucket
    try:
        job_dir = create_job_dir(args.job_id)
    except:
        logger.error('Unable to create job dir')
        raise

    # The cleanup argument is overriden to False if an s3bucket argument is not
    # given. Doing so preserves experiment results.
    if not args.s3bucket and args.cleanup:
        logger.info('An S3 bbucket is not given. Cleanup of the Temporary Job' \
                    ' Dir will be skipped in order to preserve job results.')
        args.cleanup = False

    if args.cleanup:
        logger.info('Clean up will be done on exit.')
        atexit.register(clean_up, job_dir)
    else:
        logger.info('Clean up will NOT be done on exit.')
     
    experiments = {}
    if args.experiments: 
        experiments = args.experiments
    # Run experiments
    run_experiments(args.pool, job_dir, experiments)
    # Process results
    process_results(job_dir, args.s3bucket)


# **************
# *  UNIT TESTS !!!!! (use -t to run them)
# ***************
def test():
    print("The 'unittest' module is not available!\nUnable to run tests!")
    return 0


try:
    import unittest

    def test(args, module='__main__'):
        t = unittest.main(argv=['chaosindy_test'], module=module, exit=False,
                          verbosity=10)
        return int(not t.result.wasSuccessful())

    class ErrorRaisingArgumentParser(argparse.ArgumentParser):
        # Override error so it does NOT exit! Doing so allows for invalid
        # argparse input scenarios to be tested.
        def error(self, message):
            # Reraise the error
            raise ValueError(message)

    class TestRun(unittest.TestCase):
        test_pool = "test_pool1"
        temp_dir = None

        @classmethod
        def setUpClass(cls):
            sys.stderr = StringIO()
            logger.setLevel(sys.maxsize)
            temp_dir = tempfile.TemporaryDirectory()
            pass

        @classmethod
        def tearDownClass(cls):
            pass

        # TODO: need any static methods?
        #@staticmethod

        def test_arg_log_level(self):
            for k, v in levels.items():
                test_args = parse_args([self.test_pool, '-l', k])
                self.assertEqual(test_args.log_level, v)

            test_args = parse_args([self.test_pool, '-l'])
            self.assertEqual(test_args.log_level, logging.INFO,
                             msg='Invalid const level')
            test_args = parse_args([self.test_pool])
            self.assertEqual(test_args.log_level, logging.INFO,
                             msg='Invalid default level')

        def test_experiments_dict(self):
            script_path = os.path.dirname(os.path.realpath(__file__))
            run_script = os.path.join(script_path,
                                      'scripts/run-force-view-change')
            experiments_dict_in = {
                'path': [
                    script_path
                ],
                'experiments': {
                    'force-view-change': {
                        'execution-count': 3
                    }
                }
            }
            experiments_dict_out = {
                'force-view-change': {
                    'run_script': run_script,
                    'execution-count': 3
                }
            }
            test_args = parse_args([self.test_pool, '--experiments',
                                    json.dumps(experiments_dict_in)])
            self.assertEqual(test_args.experiments, experiments_dict_out)

        def test_experiments_dict_invalid_path(self):
            # invalid path
            # Create an empty temporary directory and use it in the 'path'
            temp_dir = tempfile.TemporaryDirectory()
            experiments_dict_in = {
                'path': [temp_dir.name]
            }
            # Expect and exception
            with self.assertRaises(ValueError) as e:
                test_args = parse_args(argv=[self.test_pool, '--experiments',
                    json.dumps(experiments_dict_in)],
                    parser=program_args(parser=ErrorRaisingArgumentParser()))
            self.assertEqual(str(e.exception), "argument --experiments: " \
                "Invalid 'path' element. The following directories do not " \
                "contain a 'scripts' sub-directory: ['{}']".format(
                temp_dir.name))
            # Add a 'scripts' subdirectory to the temporary directory and
            # Assert that parse_args passes w/o any exceptions
            os.mkdir(os.path.join(temp_dir.name, "scripts"))
            test_args = parse_args(argv=[self.test_pool, '--experiments',
                json.dumps(experiments_dict_in)],
                parser=program_args(parser=ErrorRaisingArgumentParser()))
            self.assertEqual(test_args.experiments, {})
            # Cleanup
            shutil.rmtree(temp_dir.name)

        def test_experiments_dict_name_invalid_experiment(self):
            # invalid experiment (does not exist)
            # Create a temporary directory that contains an empty scripts
            # subdirectory.
            temp_dir = tempfile.TemporaryDirectory()
            os.makedirs(os.path.join(temp_dir.name, "scripts"))
            experiments_dict_in = {
                'path': [temp_dir.name],
                'experiments': {
                    'foo': {}
                }
            }
            # Expect an exception
            with self.assertRaises(ValueError) as e:
                test_args = parse_args(argv=[self.test_pool, '--experiments',
                    json.dumps(experiments_dict_in)],
                    parser=program_args(parser=ErrorRaisingArgumentParser()))
            self.assertEqual(str(e.exception), "argument --experiments: " \
                "Invalid 'experiments' element. The following experiments do " \
                "not exist: ['foo']")
            # Add a "run-foo" file to the scripts directory
            run_script = os.path.join(temp_dir.name, "scripts", "run-foo")
            open(run_script, 'a').close()
            # Assert that parse_args passes w/o any exceptions
            test_args = parse_args(argv=[self.test_pool, '--experiments',
                json.dumps(experiments_dict_in)],
                parser=program_args(parser=ErrorRaisingArgumentParser()))
            experiments_dict_out = {
                'foo': {
                    'run_script': run_script
                }
            }
            self.assertEqual(test_args.experiments, experiments_dict_out)
            # Cleanup
            shutil.rmtree(temp_dir.name)

        def test_experiments_dict_discover_experiments(self):
            # w/o explicit set of tests to run. Discover all tests.
            # Create a temporary directory 1 that contains a scripts
            # subdirectory containing a run-foo script/file.
            temp_dir1 = tempfile.TemporaryDirectory()
            os.makedirs(os.path.join(temp_dir1.name, "scripts"))
            # Add a "run-foo" file to the scripts directory
            run_script1 = os.path.join(temp_dir1.name, "scripts", "run-foo")
            open(run_script1, 'a').close()
            # Create a temporary directory 2 that contains a scripts
            # subdirectory containing a run-foo script/file.
            temp_dir2 = tempfile.TemporaryDirectory()
            os.makedirs(os.path.join(temp_dir2.name, "scripts"))
            # Add a "run-foo" file to the scripts directory
            run_script2 = os.path.join(temp_dir2.name, "scripts", "run-bar")
            open(run_script2, 'a').close()
            experiments_dict_in = {
                'path': [temp_dir1.name, temp_dir2.name]
            }
            # Assert that parse_args passes w/o any exceptions and that
            # experiment foo was found
            test_args = parse_args(argv=[self.test_pool, '--experiments',
                json.dumps(experiments_dict_in)],
                parser=program_args(parser=ErrorRaisingArgumentParser()))
            experiments_dict_out = {
                'foo': {
                    'run_script': run_script1
                },
                'bar': {
                    'run_script': run_script2
                }
            }
            self.assertEqual(test_args.experiments, experiments_dict_out)
            # Cleanup
            shutil.rmtree(temp_dir1.name)

        def test_experiments_dict_exclude_experiment(self):
            # exclude experiment
            # Create a temporary directory that contains a scripts  subdirectory
            # containing a run-foo script/file.
            temp_dir = tempfile.TemporaryDirectory()
            os.makedirs(os.path.join(temp_dir.name, "scripts"))
            # Add a "run-foo" file to the scripts directory
            run_script = os.path.join(temp_dir.name, "scripts", "run-foo")
            open(run_script, 'a').close()
            experiments_dict_in = {
                'path': [temp_dir.name],
                'exclude': ['foo']
            }
            # Assert that parse_args passes w/o any exceptions and that
            # experiment foo was found
            test_args = parse_args(argv=[self.test_pool, '--experiments',
                json.dumps(experiments_dict_in)],
                parser=program_args(parser=ErrorRaisingArgumentParser()))
            experiments_dict_out = {}
            self.assertEqual(test_args.experiments, experiments_dict_out)
            # Cleanup
            shutil.rmtree(temp_dir.name)

        def test_experiments_dict_exclude_invalid_experiment(self):
            # invalid exclude experiment. (does not exist)
            # Create a temporary directory that contains a scripts  subdirectory
            # containing a run-foo script/file.
            temp_dir = tempfile.TemporaryDirectory()
            os.makedirs(os.path.join(temp_dir.name, "scripts"))
            experiments_dict_in = {
                'path': [temp_dir.name],
                'exclude': ['foo']
            }
            # Assert that parse_args fails with an exception stating experiment
            # foo was found
            with self.assertRaises(ValueError) as e:
                test_args = parse_args(argv=[self.test_pool, '--experiments',
                    json.dumps(experiments_dict_in)],
                    parser=program_args(parser=ErrorRaisingArgumentParser()))
            self.assertEqual(str(e.exception), "argument --experiments: " \
                "Invalid 'exclude' element. The following experiments do " \
                "not exist: ['foo']")
            # Cleanup
            shutil.rmtree(temp_dir.name)

        def test_create_job_dir(self):
            build_tag = "foo"
            delimiter = "-"
            job_dir_path = create_job_dir(build_tag)
            self.assertTrue(os.path.exists(job_dir_path))

            try:
                tokens = job_dir_path.split(delimiter)
                create_datetime = delimiter.join(tokens[1:])
                create_datetime = create_datetime[0:-8]
                create_datetime = dateutil.parser.parse(create_datetime)
            except Exception as error:
                self.fail("Failed to extract and parse ISO 8601 datetime from" \
                          " temporary directory created by create_job_dir.")

            now_datetime = datetime.datetime.now()
            self.assertAlmostEqual(create_datetime, now_datetime,
                                   delta=datetime.timedelta(seconds=5))

        def test_default_experiments(self):
            experiments = default_experiments()
            self.assertEqual(type(experiments), dict)
            for k, v in experiments.items():
                self.assertEqual(type(v), dict)
                self.assertEqual(list(v.keys()), ['run_script'])

except ImportError:
    pass

if __name__ == '__main__':
    arguments = parse_args()

    if arguments.test:
        exit_code = test(arguments)
        sys.exit(exit_code)
    else:
        sys.exit(main(arguments))
