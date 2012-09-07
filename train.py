import numpy as np
import matplotlib as mpl
mpl.use('Agg')
#from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cross_validation import train_test_split, ShuffleSplit
from sklearn.grid_search import GridSearchCV
#from sklearn.cross_validation import cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from features import TextFeatureTransformer
from sklearn.metrics import auc_score
#from sklearn.svm import LinearSVC
import matplotlib.pyplot as plt


from time import strftime
from IPython.core.debugger import Tracer


tracer = Tracer()


def load_data():
    print("loading")
    comments = []
    dates = []
    labels = []

    #with codecs.open("train.csv", encoding="utf-8") as f:
    with open("train.csv") as f:
        f.readline()
        for line in f:
            splitstring = line.split(',')
            labels.append(splitstring[0])
            dates.append(splitstring[1][:-1])
            comment = ",".join(splitstring[2:])
            comment = comment.strip().strip('"')
            comment.replace('_', ' ')
            comment = comment.replace("\\\\", "\\")
            comment = comment.decode('unicode-escape')
            comments.append(comment)
    labels = np.array(labels, dtype=np.int)
    dates = np.array(dates)
    return comments, dates, labels


def load_test():
    print("loading test set")
    comments = []
    dates = []

    with open("test.csv") as f:
        f.readline()
        for line in f:
            splitstring = line.split(',')
            dates.append(splitstring[0][:-1])
            comment = ",".join(splitstring[1:])
            comment = comment.strip().strip('"')
            comment.replace('_', ' ')
            comment.replace('.', ' ')
            comment = comment.replace("\\\\", "\\")
            comment = comment.decode('unicode-escape')
            comments.append(comment)
    dates = np.array(dates)
    return comments, dates


def write_test(labels, fname=None):
    if fname is None:
        fname = "test_prediction_september_%s.csv" % strftime("%d_%H_%M")
    with open("test.csv") as f:
        with open(fname, 'w') as fw:
            f.readline()
            fw.write("Insult,Date,Comment\n")
            for label, line in zip(labels, f):
                fw.write("%f," % label)
                fw.write(line)


def jellyfish():
    import jellyfish

    comments, dates, labels = load_data()
    y_train, y_test, comments_train, comments_test = \
            train_test_split(labels, comments)
    ft = TextFeatureTransformer(word_range=(1, 1),
            tokenizer_func=jellyfish.metaphone).fit(comments_train)
    tracer()
    clf = LogisticRegression(C=1, tol=1e-8)
    X_train = ft.transform(comments_train)
    clf.fit(X_train, y_train)
    X_test = ft.transform(comments_test)
    probs = clf.predict_proba(X_test)
    print("auc: %f" % auc_score(y_test, probs[:, 1]))


def test_bagging():
    comments, dates, labels = load_data()
    comments = np.asarray(comments)
    cv = ShuffleSplit(len(comments), n_iterations=20, test_size=0.2, indices=True)
    clf = LogisticRegression(tol=1e-8, penalty='l2', C=0.5)
    ft = TextFeatureTransformer(char=True, word=True, designed=True,
            word_range=(1, 3), char_range=(1, 5))
    pipeline = Pipeline([('vect', ft), ('logr', clf)])
    clf2 = LogisticRegression(tol=1e-8, penalty='l2', C=4)
    ft2 = TextFeatureTransformer(char=True, word=False, designed=True, char_range=(1, 4))
    pipeline2 = Pipeline([('vect', ft2), ('logr', clf2)])
    clf3 = LogisticRegression(tol=1e-8, penalty='l2', C=1)
    ft3 = TextFeatureTransformer(char=False, word=True, designed=True, word_range=(1, 2))
    pipeline3 = Pipeline([('vect', ft3), ('logr', clf3)])
    joint = []
    words = []
    chars = []
    combined = []
    all = []
    for train, test in cv:
        X_train, y_train = comments[train], labels[train]
        X_test, y_test = comments[test], labels[test]
        pred = pipeline.fit(X_train, y_train).predict_proba(X_test)[:, 1]
        pred2 = pipeline2.fit(X_train, y_train).predict_proba(X_test)[:, 1]
        pred3 = pipeline3.fit(X_train, y_train).predict_proba(X_test)[:, 1]
        joint.append(auc_score(y_test, pred))
        words.append(auc_score(y_test, pred3))
        chars.append(auc_score(y_test, pred2))
        combined.append(auc_score(y_test, pred2 + pred3))
        all.append(auc_score(y_test, pred2 + pred3 + pred))
        print("together: %f, first: %f, second:%f, combined: %f all: %f" %
                (joint[-1], chars[-1], words[-1], combined[-1], all[-1]))
    tracer()




def grid_search():
    #from sklearn.linear_model import SGDClassifier
    from sklearn.feature_selection import SelectPercentile, chi2
    #import jellyfish as jf
    comments, dates, labels = load_data()
    #param_grid = dict(logr__C=np.arange(1, 20),
            #select__percentile=np.arange(2, 17, 1))
    #param_grid = dict(logr__C=2. ** np.arange(0, 8), vect__char_range=[(1, 5)],
            #vect__word_range=[(1, 3)], select__percentile=np.arange(1, 70,
                #5))
    param_grid = dict(logr__C=2. ** np.arange(0, 8), vect__char_range=[(1, 5)],
            vect__word_range=[(1, 3)])
    #param_grid = dict(logr__C=2. ** np.arange(-6, 0), vect__word_range=[(1, 1),
       #(1, 2), (1, 3), (2, 3), (3, 3)], vect__char_range=[(1, 1), (1, 2), (1,
           #3), (1, 4), (1, 5), (2, 2), (2, 3), (2, 4), (2, 5)])
    clf = LogisticRegression(tol=1e-8, penalty='l2')
    ft = TextFeatureTransformer(char=True, word=True, designed=True,
            char_range=(1, 5), word_range=(1, 3))
    select = SelectPercentile(score_func=chi2)
    #pipeline = Pipeline([('vect', ft), ('select', select), ('logr', clf)])
    pipeline = Pipeline([('select', select), ('logr', clf)])
    #pipeline = Pipeline([('vect', ft), ('logr', clf)])
    cv = ShuffleSplit(len(comments), n_iterations=20, test_size=0.2)
    grid = GridSearchCV(pipeline, cv=cv, param_grid=param_grid, verbose=4,
            n_jobs=12, score_func=auc_score)
    X = ft.fit(comments).transform(comments)
    grid.fit(X, labels)
    print(grid.best_score_)
    print(grid.best_params_)
    #comments_test, dates_test = load_test()
    #prob_pred = grid.best_estimator_.predict_proba(comments_test)
    #write_test(prob_pred[:, 1])
    c_mean, c_err = grid.scores_.accumulated('logr__C')
    c_values = grid.scores_.values['logr__C']
    plt.errorbar(c_values, c_mean, yerr=c_err)
    plt.ylim(0.85, 0.93)
    plt.savefig("grid_plot.png")
    plt.close()
    #w_mean, w_err = grid.scores_.accumulated('vect__word_range')
    #w_values = np.arange(len(grid.scores_.values['vect__word_range']))
    #plt.errorbar(w_values, w_mean, yerr=w_err)
    #plt.ylim(0.81, 0.91)
    #plt.savefig("grid_plot_w.png")
    #plt.close()
    #w_mean, w_err = grid.scores_.accumulated('vect__char_range')
    #w_values = np.arange(len(grid.scores_.values['vect__char_range']))
    #plt.errorbar(w_values, w_mean, yerr=w_err)
    #plt.ylim(0.85, 0.93)
    #plt.savefig("grid_plot_c.png")
    #plt.close()
    w_mean, w_err = grid.scores_.accumulated('logr__tol')
    w_values = np.arange(len(grid.scores_.values['logr__tol']))
    plt.errorbar(w_values, w_mean, yerr=w_err)
    plt.ylim(0.85, 0.93)
    plt.savefig("grid_plot_tol.png")
    plt.close()
    tracer()
    comments_test, dates_test = load_test()
    prob_pred = grid.best_estimator_.predict_proba(comments_test)
    write_test(prob_pred[:, 1])


def analyze_output():
    comments, dates, labels = load_data()
    y_train, y_test, comments_train, comments_test = \
            train_test_split(labels, comments)
    #clf = LogisticRegression(tol=1e-8, penalty='l1', C=0.5)
    clf = LogisticRegression(tol=1e-8, penalty='l1', C=32)
    ft = TextFeatureTransformer(char=False, word=False, char_max_n=4,
            word_max_n=3, char_min_n=3).fit(comments_train)
    X_train = ft.transform(comments_train)
    clf.fit(X_train, y_train)
    X_test = ft.transform(comments_test)
    probs = clf.predict_proba(X_test)
    pred = clf.predict(X_test)
    print("auc: %f" % auc_score(y_test, probs[:, 1]))

    fp = np.where(pred > y_test)[0]
    fn = np.where(pred < y_test)[0]
    fn_comments = comments_test[fn]
    fp_comments = comments_test[fp]
    n_bad = X_test[:, -2].toarray().ravel()
    fn_comments = np.vstack([fn, n_bad[fn], probs[fn][:, 1], fn_comments]).T
    fp_comments = np.vstack([fp, n_bad[fp], probs[fp][:, 1], fp_comments]).T

    # visualize important features
    important = np.abs(clf.coef_.ravel()) > 0.001
    #important = np.abs(clf.coef_.ravel()) > 0.5
    feature_names = ft.get_feature_names()

    f_imp = feature_names[important]
    coef = clf.coef_.ravel()[important]
    inds = np.argsort(coef)
    f_imp = f_imp[inds]
    coef = coef[inds]
    plt.plot(coef)
    ax = plt.gca()
    ax.set_xticks(np.arange(len(coef)))
    labels = ax.set_xticklabels(f_imp)
    for label in labels:
        label.set_rotation(90)
    plt.show()

    tracer()


if __name__ == "__main__":
    grid_search()
    #analyze_output()
    #grid_search_feature_selection()
    #feature_selection_test()
    #jellyfish()
    #test_bagging()
