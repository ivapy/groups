import numpy as np
from scipy.linalg import expm
import matplotlib.pyplot as plt

import pdb

class Homog:
    def __init__(self, *args, **kwargs):
        if(len(kwargs) == 0):
            self.__M = np.eye(4)
        elif(len(kwargs) == 2):
            R = kwargs['R']
            x = kwargs['x']
            if(np.shape(R) != (3,3)):
                raise ValueError("Rotation Matrix must be orthogonal 3x3 matrix")
            if(np.shape(x) != (3,1)):
                raise ValueError("Displacement must be 3x1 vector")

            self.__M = np.hstack((R, x))
            self.__M = np.vstack((self.__M, np.array([0,0,0,1])))
        elif(len(kwargs) == 1):
            M = kwargs['M']
            if(np.shape(M) == (4,4) and np.array_equal(M[3,:], np.array([0, 0, 0, 1]))):
                self.__M = M
            else:
                raise ValueError("Not a Homogenous matrix")
    
    def getTranslation(self):
        return self.__M[0:3, 3][:,np.newaxis]
    
    def getRotation(self):
        return self.__M[0:3, 0:3]

    def getRPY(self):
        rot = self.getRotation()
        roll = np.arctan2(rot[2, 1], rot[2, 2])
        pitch = np.arctan2(-rot[2, 0], np.sqrt(rot[2,1]**2 + rot[2,2]**2))
        yaw = np.arctan2(rot[1,0], rot[0, 0])
        return (roll, pitch, yaw)

    def __mul__(self, other):
        if(type(other) == Homog):
            m = np.matmul(self.__M, other.__M)
            return Homog(M=m)
        elif(type(other) == np.ndarray):
            if(np.shape(np.squeeze(other)) == (3,)): # Point in 3D
                vec = np.vstack((other[:, np.newaxis], [1]))
                return np.matmul(self.__M, vec)[:-1]
            elif np.array(other).ndim == 2 and np.shape(other)[0] == 3: # 2D Matrix of Points
                vec = np.vstack((other, np.ones((1,np.shape(other)[1]))))
                return np.matmul(self.__M, vec)[:-1]
    
    def plot(self, ax=None, scale=1):
        o = self.getTranslation()
        p1 = self*np.array([scale,0,0])
        p2 = self*np.array([0,scale,0])
        p3 = self*np.array([0,0,scale])
        pts = np.hstack((o, p1, o, p2, o, p3))
        ax.plot(pts[0,:],pts[1,:],pts[2,:], '--')

    def __str__(self):
        return str(self.__M)
    
    def inv(self):
        return Homog(M=np.linalg.inv(self.__M))

    def log(self, tau=1):
        normw = np.arccos( (np.trace(self.getRotation())-1)/2 ) / tau
        if (normw == 0):            # If rotation, pure translation.
            w = np.zeros((3, 1))
            v = self.__M[np.newaxis, 0:3,3].T/tau
        else:                       # else, use logarithm equation
            #--(1) First do the log of the rotation matrix.
            hatw = (normw/(2*np.sin(normw*tau)))*(self.getRotation() - self.getRotation().T)
            w = np.vstack((hatw[2,1] , hatw[0,2] , hatw[1,0]))

            #--(2) Second, use both hat omega and omega to get the velocity.
            v = (normw**2)*np.matmul(np.linalg.inv(np.matmul((np.eye(3) - self.getRotation()),hatw) + tau*w*w.T), self.getTranslation())
        return np.vstack((v, w))

    @staticmethod 
    def hat(xiVec):
        omegaHat = np.vstack((np.hstack((0, -xiVec[5], xiVec[4])), np.hstack((xiVec[5], 0, -xiVec[3])), \
               np.hstack((-xiVec[4], xiVec[3], 0))))
        #pdb.set_trace()
        xiHat = np.hstack((omegaHat, xiVec[0:3]))
        return np.vstack((xiHat, np.array([0,0,0,0])))

    @staticmethod 
    def exp(xi, t=1): # xi is a Lie Algebra
        if(np.shape(np.squeeze(xi)) == (6,)):
            xi = Homog.hat(xi)
        #pdb.set_trace()
        expMat = expm(xi*t)
        return Homog(M=expMat)

    @staticmethod
    def RotX(theta):
        return np.array([[1, 0, 0], [0, np.cos(theta), -np.sin(theta)], [0, np.sin(theta), np.cos(theta)]])

    @staticmethod
    def RotY(theta):
        return np.array([[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], [-np.sin(theta), 0, np.cos(theta)]])

    @staticmethod
    def RotZ(theta):
        return np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])