from test_tube import Experiment, HyperOptArgumentParser, SlurmCluster

"""
Example script to show how to run a hyperparameter search on a cluster managed by SLURM

Every distinct set of hyperparams runs on the configured hardware described in the SlurmCluster set up
"""


# main training function (very simple)
def train(hparams):

    # this won't crash ever. If no exp number is there, it'll be None
    exp_version_from_slurm_script = hparams.hpc_exp_number

    # init exp and track all the parameters from the HyperOptArgumentParser
    # the experiment version is optional, but using the one from slurm means the exp will not collide with other
    # versions if slurm runs multiple at once.
    exp = Experiment(
        name=hparams.test_tube_exp_name,
        save_dir=hparams.log_path,
        version=exp_version_from_slurm_script,
        autosave=False,
    )
    exp.argparse(hparams)

    # pretend to train
    x = hparams.x_val
    for train_step in range(0, 100):
        y = hparams.y_val
        out = x * y
        exp.log({'fake_err': out.item()})

    # save exp when we're done
    exp.save()


# set up our argparser and make the y_val tunable
parser = HyperOptArgumentParser(strategy='random_search')
parser.add_argument('--test_tube_exp_name', default='my_test')
parser.add_argument('--log_path', default='/some/path/to/log')
parser.opt_list('--y_val', default=12, options=[1, 2, 3, 4, 5, 6], tunable=True)
parser.opt_list('--x_val', default=12, options=[20, 12, 30, 45], tunable=True)
hyperparams = parser.parse_args()

# enable cluster training
cluster = SlurmCluster(
    hyperparam_optimizer=hyperparams,
    log_path=hyperparams.log_path,
    python_cmd='python3',
    test_tube_exp_name=hyperparams.test_tube_exp_name
)

# email results if your hpc supports it
cluster.notify_job_status(email='some@email.com', on_done=True, on_fail=True)

# any modules for code to run in env
cluster.load_modules([
    'python-3',
    'anaconda3'
])
# add commands to the non slurm portion
cluster.add_command('source activate myCondaEnv')

# can also add custom slurm commands which show up as:
# #comment
# #SBATCH --cmd=value
# ############
# cluster.add_slurm_cmd(cmd='cpus-per-task', value='1', comment='nb cpus per task')

# set job compute details (this will apply PER set of hyperparameters)
cluster.per_experiment_nb_cpus = 20
cluster.per_experiment_nb_nodes = 10

# each job (24 in total here) will use 200 cpus for each set of hyperparams
# if job_display_name is set, it's what will display in the slurm queue
cluster.optimize_parallel_cluster_cpu(train, nb_trials=24, job_name='first_tt_job', job_display_name='short_name')
