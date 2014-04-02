from Tools import Logger
from ValueEstimators.TDLearning import TDLearning
from Representations import HashedTabular
from Domains import PST
from Tools import __rlpy_location__
from Experiments.PolicyEvaluationExperiment import PolicyEvaluationExperiment
from Policies import StoredPolicy
import numpy as np
from hyperopt import hp

param_space = {'lambda_': hp.uniform("lambda_", 0., 1.),
               'boyan_N0': hp.loguniform("boyan_N0", np.log(1e1), np.log(1e5)),
               'initial_alpha': hp.loguniform("initial_alpha", np.log(1e-2), np.log(1))}


def make_experiment(id=1, path="./Results/Temp/{domain}/poleval/ifdd/",
                    lambda_=0.701309,
                    boyan_N0=1375.098,
                    initial_alpha=0.016329):
    logger = Logger()
    max_steps = 500000
    sparsify = 1
    domain = PST(NUM_UAV=4, motionNoise=0, logger=logger)
    pol = StoredPolicy(filename="__rlpy_location__/Policies/PST_4UAV_mediocre_policy_nocache.pck")
    representation = HashedTabular(domain, logger, memory=40000, safety="super")
    estimator = TDLearning(representation=representation, lambda_=lambda_,
                           boyan_N0=boyan_N0, initial_alpha=initial_alpha, alpha_decay_mode="boyan")
    experiment = PolicyEvaluationExperiment(estimator, domain, pol, max_steps=max_steps, num_checks=20,
                                            path=path, log_interval=10, id=id)
    experiment.num_eval_points_per_dim=20
    experiment.num_traj_V = 300
    experiment.num_traj_stationary = 300
    return experiment

if __name__ == '__main__':
    from Tools.run import run_profiled
    #run_profiled(make_experiment)
    experiment = make_experiment(1)
    experiment.run()
    #experiment.plot()
    #experiment.save()