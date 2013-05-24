"""
WORK IN PROGRESS
"""


import sys
import os
#Add all paths
RL_PYTHON_ROOT = '.'
while not os.path.exists(RL_PYTHON_ROOT + '/RLPy/Tools'):
    RL_PYTHON_ROOT = RL_PYTHON_ROOT + '/..'
RL_PYTHON_ROOT += '/RLPy'
RL_PYTHON_ROOT = os.path.abspath(RL_PYTHON_ROOT)
sys.path.insert(0, RL_PYTHON_ROOT)

from Tools import *
from Domain import *
import numpy as np
import matplotlib.pyplot as plt

class Acrobot(Domain):
    """
    Acrobot is a 2-link pendulum with only the second joint actuated
    Intitially, both links point downwards. The goal is to swing the
    end-effector at a height at least the length of one link above the base.

    The state consists of the two rotational joint angles and their velocities
    [theta1 theta2 dtheta1 dtheta2]

    for details see R. Sutton: Generalization in Reinforcement Learning:
        Successful Examples Using Sparse Coarse Coding (NIPS 1996)
    """

    episodeCap = 1000
    dt = .2
    continuous_dims = np.arange(4)

    LINK_LENGTH_1 = 1. # [m]
    LINK_LENGTH_2 = 1. #[m]
    LINK_MASS_1 = 1. # [kg]
    LINK_MASS_2 = 1. # [kg]
    LINK_COM_POS_1 = 0.5 # [m] position of the center of mass of the links
    LINK_COM_POS_2 = 0.5 # [m] position of the center of mass of the links
    LINK_MOI = 1. # moments of inertia

    MAX_VEL_1 = 4*np.pi
    MAX_VEL_2 = 9*np.pi

    AVAIL_TORQUE = [-1., 0., +1]

    torque_noise_max = 0.
    statespace_limits = np.array([[-np.pi, np.pi]] * 2 \
                                 + [[-MAX_VEL_1, MAX_VEL_1]] \
                                 + [[-MAX_VEL_2, MAX_VEL_2]])

    domain_fig = None
    actions_num = 3


    def s0(self):
        return np.zeros((4))


    def isTerminal(self, s):
        return -np.cos(s[0]) - np.cos(s[1]+s[0]) > 1.

    def step(self,s,a):
        # Simulate one step of the CartPole after taking action a
        # Note that at present, this is almost identical to the step for the Pendulum.

        torque = self.AVAIL_TORQUE[a]

        # Add noise to the force action
        if self.torque_noise_max > 0:
            torque += random.uniform(-self.torque_noise_max, self.torque_noise_max)

        # Now, augment the state with our force action so it can be passed to _dsdt
        s_augmented = np.append(s, torque)

        # Decomment the line below to use inbuilt runge-kutta method.
        ns = rk4(self._dsdt, s_augmented, [0, self.dt])
        ns = ns[-1] # only care about final timestep of integration returned by integrator
        ns = ns[:4] # omit action
        # ODEINT IS TOO SLOW!
        # ns_continuous = integrate.odeint(self._dsdt, self.s_continuous, [0, self.dt])
        #self.s_continuous = ns_continuous[-1] # We only care about the state at the ''final timestep'', self.dt

        ns[0] = wrap(ns[0],-np.pi,np.pi)
        ns[1] = wrap(ns[1],-np.pi,np.pi)
        ns[2] = bound(ns[2],-self.MAX_VEL_1, self.MAX_VEL_1)
        ns[3] = bound(ns[3],-self.MAX_VEL_2, self.MAX_VEL_2)
        terminal                    = self.isTerminal(ns)
        reward                      = -1. if not terminal else 0.
        return reward, ns, terminal

    def _dsdt(self, s_augmented, t):
        m1 = self.LINK_MASS_1
        m2 = self.LINK_MASS_2
        l1 = self.LINK_LENGTH_1
        l2 = self.LINK_LENGTH_2
        lc1 = self.LINK_COM_POS_1
        lc2 = self.LINK_COM_POS_2
        I1 = self.LINK_MOI
        I2 = self.LINK_MOI
        g = 9.81
        a = s_augmented[-1]
        s = s_augmented[:-1]
        d1 = m1*lc1**2 + m2*(l1**2 + lc2**2 + 2*l1*lc2*np.cos(s[1])) + I1 + I2
        d2 = m2 * (lc2**2 + l1*lc2*np.cos(s[1])) + I2
        phi2 = m2*lc2*g*np.cos(s[0]+s[1]-np.pi/2.)
        phi1 = - m2*l1*lc2*s[3]**2*np.sin(s[1]) - 2*m2*l1*lc2*s[3]*s[2]*np.sin(s[1])  \
                +(m1*lc1+m2*l1)*g*np.cos(s[0] - np.pi/2) + phi2
        ddtheta2 = (a + d2/d1*phi1 - phi2) / (m2*lc2**2 + I2 - d2**2/d1)
        ddtheta1 = -(d2*ddtheta2 + phi1) / d1
        return (s[2], s[3], ddtheta1, ddtheta2, 0.)


    def showDomain(self,s,a = 0):
        """
        Plot the 2 links
        """
        #TODO plot the action

        if self.domain_fig == None: # Need to initialize the figure
            self.domain_fig = plt.gcf()
            ax = self.domain_fig.add_axes([0, 0, 1, 1], frameon=True, aspect=1.)
            self.link1 = lines.Line2D([],[], linewidth=2, color='black')
            self.link2 = lines.Line2D([],[], linewidth=2, color='blue')
            ax.add_line(self.link1)
            ax.add_line(self.link2)

            # Allow room for pendulum to swing without getting cut off on graph
            viewable_distance = self.LINK_LENGTH_1+ self.LINK_LENGTH_2 + 0.5
            ax.set_xlim(-viewable_distance, +viewable_distance)
            ax.set_ylim(-viewable_distance, viewable_distance)
            # add bar
            bar = lines.Line2D([-viewable_distance, viewable_distance],
                                    [self.LINK_LENGTH_1, self.LINK_LENGTH_1]
                                    , linewidth=1, color='red')
            ax.add_line(bar)
            #ax.set_aspect('equal')

            plt.show()

        # update pendulum arm on figure
        p1 = [-self.LINK_LENGTH_1*np.cos(s[0]), self.LINK_LENGTH_1*np.sin(s[0])]

        self.link1.set_data([0., p1[1]],[0., p1[0]])
        p2 = [p1[0] - self.LINK_LENGTH_2*np.cos(s[0]+s[1]), p1[1] + self.LINK_LENGTH_2*np.sin(s[0]+s[1])]
        self.link2.set_data([p1[1], p2[1]], [p1[0], p2[0]])
        plt.draw()


if __name__ == "__main__":
    h = Acrobot(None)
    h.test(1000)