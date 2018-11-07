import os
import glob
import subprocess
import time
from collections import namedtuple
from logzero import logger

CLI_CMD_NAME = "indy-cli"


CliReturn = namedtuple('cli_rtn', 'std_out std_err return_code')


class CliRunner:
    def __init__(self, output_dir, cli_cmd_name: str=CLI_CMD_NAME):
        self.output_dir = output_dir
        self.cli_cmd_name = cli_cmd_name

    def _create_batch_file_name(self):
        return "cli-batch-" + str(time.time()).replace(".", "-", 1)

    def _find_available_batch_name(self, run_name: str, num_modifier: int=0):
        if num_modifier > 0:
            run_name = run_name + "-" + str(num_modifier).zfill(2)
        if len(glob.glob(os.path.join(self.output_dir, run_name)+"*")) != 0:
            run_name = self._find_available_batch_name(run_name, num_modifier=num_modifier+1)
        return run_name

    def run(self, batch: str, run_name: str=None):
        logger.info("Running batch. name: %s", run_name)

        if run_name is None:
            run_name = self._create_batch_file_name()

        run_name = self._find_available_batch_name(run_name)

        full_batch_file_path = os.path.join(self.output_dir, run_name+".cli.in")
        with open(full_batch_file_path, "w") as f:
            f.write(batch)
            f.flush()
            logger.debug("Batch file written to: %s", full_batch_file_path)

        p = subprocess.run([self.cli_cmd_name, full_batch_file_path],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           shell=False,
                           check=False
                           )

        std_out = p.stdout
        std_err = p.stderr
        return_code = p.returncode

        stdout_file_path = os.path.join(self.output_dir, run_name+".cli.out")

        with open(stdout_file_path, "wb") as f:
            f.write(std_out)
            f.flush()
            logger.debug("CLI stdout written to: %s", stdout_file_path)


        return CliReturn(std_out, std_err, return_code)