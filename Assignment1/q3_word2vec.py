#!/usr/bin/env python

import numpy as np
import random

from q1_softmax import softmax
from q2_gradcheck import gradcheck_naive
from q2_sigmoid import sigmoid, sigmoid_grad
import time

def normalizeRows(x):
    """ Row normalization function

    Implement a function that normalizes each row of a matrix to have
    unit length.
    """

    ### YOUR CODE HERE

    # def get_row_len(y):
    # 	row_len = np.apply_along_axis(lambda r: np.sqrt(np.sum(r ** 2)), 1, x)
    # 	return row_len

    # row_length = get_row_len(x).reshape(-1,1)
    # x = x/row_length

    length = np.sqrt(np.sum(np.square(x),axis=1)).reshape(-1,1)
    x = x / length

    ### END YOUR CODE

    return x


def test_normalize_rows():
    print("Testing normalizeRows...")
    x = normalizeRows(np.array([[3.0,4.0],[1, 2]]))
    print(x)
    ans = np.array([[0.6,0.8],[0.4472136,0.89442719]])
    assert np.allclose(x, ans, rtol=1e-05, atol=1e-06)
    print("")


def softmaxCostAndGradient(predicted, target, outputVectors, dataset):
    """ Softmax cost function for word2vec models

    Implement the cost and gradients for one predicted word vector
    and one target word vector as a building block for word2vec
    models, assuming the softmax prediction function and cross
    entropy loss.

    Arguments:
    predicted -- numpy ndarray, predicted word vector (\hat{v} in
                 the written component)
    target -- integer, the index of the target word
    outputVectors -- "output" vectors (as rows) for all tokens
    dataset -- needed for negative sampling, unused here.

    Return:
    cost -- cross entropy cost for the softmax word prediction
    gradPred -- the gradient with respect to the predicted word
           vector
    grad -- the gradient with respect to all the other word
           vectors

    We will not provide starter code for this function, but feel
    free to reference the code you previously wrote for this
    assignment!
    """

    ### YOUR CODE HERE
    # get y_hat
    y_hat = softmax(np.dot(outputVectors, predicted))

    # get cost
    cost = -np.log(y_hat[target])
    y_hat[target] -= 1

    # get gradPred
    gradPred = np.dot(y_hat, outputVectors)

    # get grad
    grad = np.outer(y_hat, predicted)

    ### END YOUR CODE

    return cost, gradPred, grad


def getNegativeSamples(target, dataset, K):
    """ Samples K indexes which are not the target """

    indices = [None] * K
    for k in range(K):
        newidx = dataset.sampleTokenIdx()
        while newidx == target:
            newidx = dataset.sampleTokenIdx()
        indices[k] = newidx
    return indices


def negSamplingCostAndGradient(predicted, target, outputVectors, dataset,
                               K=10):
    """ Negative sampling cost function for word2vec models

    Implement the cost and gradients for one predicted word vector
    and one target word vector as a building block for word2vec
    models, using the negative sampling technique. K is the sample
    size.

    Note: See test_word2vec below for dataset's initialization.

    Arguments/Return Specifications: same as softmaxCostAndGradient
    """

    # Sampling of indices is done for you. Do not modify this if you
    # wish to match the autograder and receive points!
    indices = [target]
    indices.extend(getNegativeSamples(target, dataset, K))

    ### YOUR CODE HERE
    # define delta1 and delta2
    delta1 = sigmoid(np.dot(outputVectors[indices[0],], predicted.reshape(-1,1)))
    delta2 = sigmoid(np.dot(outputVectors[indices[1:],], predicted.reshape(-1,1)))

    # get cost
    cost = - np.log(delta1)- np.sum(np.log(1-delta2))

    # get gradPred
    gradPred = (delta1-1) \
			* outputVectors[indices[0],] \
			+ np.sum(delta2 * outputVectors[indices[1:],], axis = 0) 

    # get grad
    grad = np.zeros(outputVectors.shape)
    grad[indices[0],:] = (delta1-1) * predicted
    for neg in range(delta2.shape[0]):
    	grad[indices[1:][neg],:] += delta2[neg,0] * predicted

    # get cost
    # cost = -np.log(sigmoid(np.dot(outputVectors[indices[0],], predicted.reshape(-1,1)))) \
		# - np.sum(np.log(sigmoid(-np.dot(outputVectors[indices[1:],], predicted.reshape(-1,1)))))

	# get gradPred
    # gradPred = (sigmoid(np.dot(outputVectors[indices[0],],predicted.reshape(-1,1)))-1) \
    # 			* outputVectors[indices[0],] \
    # 			+ np.sum(sigmoid(np.dot(outputVectors[indices[1:],], predicted.reshape(-1,1))) * outputVectors[indices[1:],], axis = 0) 

    # grad[indices[0],:] = (sigmoid(np.dot(outputVectors[indices[0],],predicted))-1) * predicted
    # for neg in indices[1:]:
    # 	grad[neg,:] += sigmoid(np.dot(outputVectors[neg,],predicted)) * predicted




    # gradPred = np.zeros_like(predicted)
    # grad = np.zeros_like(outputVectors)

    # indices = [target]
    # for k in range(K):
    #     newidx = dataset.sampleTokenIdx()
    #     while newidx == target:
    #         newidx = dataset.sampleTokenIdx()
    #     indices += [newidx]

    # directions = np.array([1] + [-1 for k in range(K)])

    # V = np.shape(outputVectors)[0]
    # N = np.shape(outputVectors)[1]

    # outputWords = outputVectors[indices,:]

    # delta = sigmoid(np.dot(outputWords,predicted) * directions)
    # deltaMinus = (delta - 1) * directions;
    # cost = -np.sum(np.log(delta));

    # gradPred = np.dot(deltaMinus.reshape(1,K+1),outputWords).flatten()
    # gradMin = np.dot(deltaMinus.reshape(K+1,1),predicted.reshape(1,N))

    # for k in range(K+1):
    #     grad[indices[k]] += gradMin[k,:]
    ### END YOUR CODE
    return cost, gradPred, grad


def skipgram(currentWord, C, contextWords, tokens, inputVectors, outputVectors,
             dataset, word2vecCostAndGradient=softmaxCostAndGradient):
    """ Skip-gram model in word2vec

    Implement the skip-gram model in this function.

    Arguments:
    currrentWord -- a string of the current center word
    C -- integer, context size
    contextWords -- list of no more than 2*C strings, the context words
    tokens -- a dictionary that maps words to their indices in
              the word vector list
    inputVectors -- "input" word vectors (as rows) for all tokens
    outputVectors -- "output" word vectors (as rows) for all tokens
    word2vecCostAndGradient -- the cost and gradient function for
                               a prediction vector given the target
                               word vectors, could be one of the two
                               cost functions you implemented above.

    Return:
    cost -- the cost function value for the skip-gram model
    grad -- the gradient with respect to the word vectors
    """

    cost = 0.0
    gradIn = np.zeros(inputVectors.shape)
    gradOut = np.zeros(outputVectors.shape)

    ### YOUR CODE HERE
    # get indice
    targets = [tokens[i] for i in contextWords]
    predicted = inputVectors[tokens[currentWord], ]

    for target in targets:
    	oneCost, gradPred, grad = word2vecCostAndGradient(predicted, target, outputVectors, dataset)
    	gradIn[tokens[currentWord],] += gradPred
    	gradOut += grad
    	cost += oneCost
    ### END YOUR CODE

    return cost, gradIn, gradOut


def cbow(currentWord, C, contextWords, tokens, inputVectors, outputVectors,
         dataset, word2vecCostAndGradient=softmaxCostAndGradient):
    """CBOW model in word2vec

    Implement the continuous bag-of-words model in this function.

    Arguments/Return specifications: same as the skip-gram model

    Extra credit: Implementing CBOW is optional, but the gradient
    derivations are not. If you decide not to implement CBOW, remove
    the NotImplementedError.
    """

    cost = 0.0
    gradIn = np.zeros(inputVectors.shape)
    gradOut = np.zeros(outputVectors.shape)

    ### YOUR CODE HERE
    # raise NotImplementedError
    ### END YOUR CODE

    return cost, gradIn, gradOut


#############################################
# Testing functions below. DO NOT MODIFY!   #
#############################################

def word2vec_sgd_wrapper(word2vecModel, tokens, wordVectors, dataset, C,
                         word2vecCostAndGradient=softmaxCostAndGradient):
    batchsize = 50
    cost = 0.0
    grad = np.zeros(wordVectors.shape)
    N = wordVectors.shape[0]
    inputVectors = wordVectors[:int(N/2),:]
    outputVectors = wordVectors[int(N/2):,:]
    for i in range(batchsize):
        C1 = random.randint(1,C)
        centerword, context = dataset.getRandomContext(C1)

        if word2vecModel == skipgram:
            denom = 1
        else:
            denom = 1

        c, gin, gout = word2vecModel(
            centerword, C1, context, tokens, inputVectors, outputVectors,
            dataset, word2vecCostAndGradient)
        cost += c / batchsize / denom
        grad[:int(N/2), :] += gin / batchsize / denom
        grad[int(N/2):, :] += gout / batchsize / denom
    return cost, grad


def test_word2vec():
    """ Interface to the dataset for negative sampling """
    dataset = type('dummy', (), {})()
    def dummySampleTokenIdx():
        return random.randint(0, 4)

    def getRandomContext(C):
        tokens = ["a", "b", "c", "d", "e"]
        return tokens[random.randint(0,4)], \
            [tokens[random.randint(0,4)] for i in range(2*C)]
    dataset.sampleTokenIdx = dummySampleTokenIdx
    dataset.getRandomContext = getRandomContext

    random.seed(31415)
    np.random.seed(9265)
    dummy_vectors = normalizeRows(np.random.randn(10,3))
    dummy_tokens = dict([("a",0), ("b",1), ("c",2),("d",3),("e",4)])
    print("==== Gradient check for skip-gram ====")
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        skipgram, dummy_tokens, vec, dataset, 5, softmaxCostAndGradient),
        dummy_vectors)
    gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
        skipgram, dummy_tokens, vec, dataset, 5, negSamplingCostAndGradient),
        dummy_vectors)
    # print("\n==== Gradient check for CBOW      ====")
    # gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
    #     cbow, dummy_tokens, vec, dataset, 5, softmaxCostAndGradient),
    #     dummy_vectors)
    # gradcheck_naive(lambda vec: word2vec_sgd_wrapper(
    #     cbow, dummy_tokens, vec, dataset, 5, negSamplingCostAndGradient),
    #     dummy_vectors)

    # print("\n=== Results ===")
    # print(skipgram("c", 3, ["a", "b", "e", "d", "b", "c"],
    #     dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset))
    # print(skipgram("c", 1, ["a", "b"],
    #     dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset,
    #     negSamplingCostAndGradient))
    # print(cbow("a", 2, ["a", "b", "c", "a"],
    #     dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset))
    # print(cbow("a", 2, ["a", "b", "a", "c"],
    #     dummy_tokens, dummy_vectors[:5,:], dummy_vectors[5:,:], dataset,
    #     negSamplingCostAndGradient))


if __name__ == "__main__":
    test_normalize_rows()
    test_word2vec()