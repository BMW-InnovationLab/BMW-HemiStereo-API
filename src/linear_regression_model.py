import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def convert_to_csv(excel_path):
    read_file = pd.read_excel(r'' + str(excel_path))
    read_file.to_csv(r'/src/dataset.csv')


def calculate_error():
    pass


def linear_regression(input):
    convert_to_csv('dataset.xlsx')
    # Importing the dataset
    dataset = pd.read_csv('dataset.csv')
    x = dataset.iloc[:, :-1].values
    y = dataset.iloc[:, -1].values

    # Splitting the dataset into the Training set and Test set
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

    # Training the Multiple Linear Regression model on the Training set
    regressor = linear_model.LinearRegression()
    regressor.fit(x_train, y_train)

    # Predicting the Test set results
    y_pred = regressor.predict(input)

    return y_pred



