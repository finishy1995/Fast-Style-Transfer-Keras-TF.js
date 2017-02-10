from keras import backend as K
from keras.regularizers import Regularizer

dummy_loss_val = K.variable(0.0)


# Dummy loss function which simply returns 0
# This is because we will be training the network using regularizers.
def dummy_loss(y_true, y_pred):
    return dummy_loss_val


def gram_matrix(x):
    assert K.ndim(x) == 3
    if K.image_dim_ordering() == 'th':
        features = K.batch_flatten(x)
    else:
        features = K.batch_flatten(K.permute_dimensions(x, (2, 0, 1)))
    gram = K.dot(features, K.transpose(features))
    return gram


class StyleReconstructionRegularizer(Regularizer):
    """ Johnson et al 2015 https://arxiv.org/abs/1603.08155 """

    def __init__(self, style_feature_target, weight=1.0):
        self.style_feature_target = style_feature_target
        self.weight = weight
        self.uses_learning_phase = False
        super(StyleReconstructionRegularizer, self).__init__()

    def __call__(self, x):
        output = x.output[0] # Generated by network
        loss = self.weight * K.mean(K.sum(K.square(gram_matrix(output) - gram_matrix(self.style_feature_target))))

        
        #assert K.ndim(output) == 3
        #assert K.ndim(self.style_feature_target) == 3
        #S = gram_matrix(style)
        #C = gram_matrix(combination)
        #channels = 3
        #size = img_nrows * img_ncols
        #return K.sum(K.square(S - C)) / (4. * (channels ** 2) * (size ** 2))
                
        return loss


class FeatureReconstructionRegularizer(Regularizer):
    """ Johnson et al 2015 https://arxiv.org/abs/1603.08155 """

    def __init__(self, weight=1.0):
        self.weight = weight
        self.uses_learning_phase = False
        super(FeatureReconstructionRegularizer, self).__init__()

    def __call__(self, x):
        generated = x.output[0] # Generated by network features
        content = x.output[1] # True X input features

        shape = K.shape(generated)
        if K.image_dim_ordering() == "th":
            channels = shape[0]
        else:
            channels = shape[-1]
        size = shape[1]

        print size, channels
        loss = self.weight * K.mean(K.sum(K.square(content - generated))) / (channels * size * size)
        
        
        
        return loss


class TVRegularizer(Regularizer):
    """ Enforces smoothness in image output. """

    def __init__(self, img_width, img_height, weight=1.0):
        self.img_width = img_width
        self.img_height = img_height
        self.weight = weight
        self.uses_learning_phase = False
        super(TVRegularizer, self).__init__()

    def __call__(self, x):
        assert K.ndim(x.output) == 4
        x_out = x.output
        if K.image_dim_ordering() == 'th':
            a = K.square(x_out[:, :, :self.img_width - 1, :self.img_height - 1] - x_out[:, :, 1:, :self.img_height - 1])
            b = K.square(x_out[:, :, :self.img_width - 1, :self.img_height - 1] - x_out[:, :, :self.img_width - 1, 1:])
        else:
            a = K.square(x_out[:, :self.img_width - 1, :self.img_height - 1, :] - x_out[:, 1:, :self.img_height - 1, :])
            b = K.square(x_out[:, :self.img_width - 1, :self.img_height - 1, :] - x_out[:, :self.img_width - 1, 1:, :])
        loss = self.weight * K.mean(K.sum(K.pow(a + b, 1.25)))
        return loss