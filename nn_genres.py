import numpy as np
import tensorflow as tf

from config import *
from os import listdir

OUTPUTS = 2
TRAINING_TRACKS = 86
TEST_TRACKS = 19

def base_NN(features, labels, test_features, test_labels, iters=1000, alpha=1e-3):

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
        print sess.run(tf.trainable_variables()[0])

    print sess.run(accuracy, feed_dict={x: test_features, y_: test_labels})
    print sess.run(y, feed_dict={x: test_features, y_: test_labels})

def main():

    x = np.array([]).reshape(TRAINING_TRACKS, 0)
    test_x = np.array([]).reshape(TEST_TRACKS, 0)

    for file in listdir('features'):
        if not file.startswith('.'):
            if file != 'pitch_features.csv':
                x = np.hstack((x, np.loadtxt(open('features/' + file, 'rb'), delimiter=',')))

    y_ = np.loadtxt(open(LABELS_FILE, 'rb'), delimiter=',')

    for file in listdir('test-features'):
        if not file.startswith('.'):
            test_x = np.hstack((test_x, np.loadtxt(open('test-features/' + file, 'rb'), delimiter=',')))

    test_y = np.zeros((TEST_TRACKS, OUTPUTS), dtype=np.int)
    test_y[:,0] = 1

    base_NN(x, y_, test_x, test_y)

if __name__ == '__main__':
    main()
