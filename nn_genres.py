import numpy as np
import tensorflow as tf

from config import *

OUTPUTS = 2

def base_NN(features, labels, iters=1000, alpha=1e-2):

    nodes = features.shape[1]

    x = tf.placeholder(tf.float32, [None, nodes])

    W = tf.Variable(tf.random_normal([nodes, OUTPUTS], stddev=0.01))
    b = tf.Variable(tf.random_normal([OUTPUTS], stddev=0.01))

    layer1 = tf.matmul(x, W) + b

    y = tf.nn.softmax(layer1)
    y_ = tf.placeholder(tf.float32, [None, OUTPUTS])

    NLL = -tf.reduce_sum(y_ * tf.log(y))

    train_step = tf.train.GradientDescentOptimizer(alpha).minimize(NLL)

    init = tf.global_variables_initializer()
    sess = tf.Session()
    sess.run(init)

    correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    for i in range(iters):
        sess.run(train_step, feed_dict={x: features, y_: labels})
        print sess.run(accuracy, feed_dict={x: features, y_: labels})
        # print sess.run(tf.trainable_variables()[0])

def main():
    x = np.loadtxt(open(FEATURES_FILE, 'rb'), delimiter=',')
    y_ = np.loadtxt(open(LABELS_FILE, 'rb'), delimiter=',')
    base_NN(x, y_)

    test_x = np.loadtxt(open(TEST_FILE, 'rb'), delimiter=',')
    

if __name__ == '__main__':
    main()
