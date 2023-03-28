import numpy as np
import pandas as pd

class ElectreI():
    def __init__(self, xls_file=None, criteria=None, criteria_description=None, alternatives_description=None, alternatives=None, W=None, agreement_threshold=None, disagreement_threshold=None):
        if xls_file is not None:
            self.read_excel(xls_file)
        else:
            if criteria is not None:
                self.set_criteria(criteria)
            else:
                self.criteria = None

            if criteria_description is not None:
                self.set_criteria_description(criteria_description)
            else:
                self.alternatives_description = None

            if alternatives_description is not None:
                self.set_alternatives_description(alternatives_description)
            else:
                self.alternatives_description = None

            if alternatives is not None:
                self.set_alternatives(alternatives)
            else:
                self.alternatives = None

            if W is not None:
                self.set_W(W)
            else:
                self.W = None

        if agreement_threshold is None:
            self.agreement_threshold = 0.5
        else:
            self.agreement_threshold = agreement_threshold

        if disagreement_threshold is None:
            self.disagreement_threshold = 0.5
        else:
            self.disagreement_threshold = disagreement_threshold

        self.normalized_alternatives = []
        self.normalized_W = []
        return

    def mount_model(self):
        self.model = pd.DataFrame(self.alternatives, columns=self.criteria_description, index=self.alternatives_description)
        self.model.index.name = 'Alternativas'
        self.model['Recomendação'] = self.recomendations[:,1]
        return

    def read_excel(self, xls_file):
        df = pd.read_excel(xls_file, index_col=0)
        self.set_criteria(np.array(df.loc['Objetivo']))
        self.set_criteria_description(np.array(df.columns))
        self.set_W(np.array(df.loc['W']))
        self.set_alternatives(df.query('Alternativas != "W" and Alternativas != "Objetivo"').to_numpy())
        self.set_alternatives_description(df.query('Alternativas != "W" and Alternativas != "Objetivo"').index.to_numpy())
        return

    def set_criteria(self, criteria):
        if criteria is not None:
            except_raised = False
            data_struct = str(type(criteria))
            if  data_struct == "<class 'list'>":
                self.criteria = np.array(criteria)
            elif data_struct == "<class 'numpy.ndarray'>":
                self.criteria = criteria
            else:
                except_raised = True
                raise Exception(f'Estrutura de dados {data_struct} não é aceita.')

            if not except_raised and self.criteria.ndim != 1:
                raise Exception(f'Dimensão igual a 1 não é aceita.')

            # Check all criteeria if differente Max or Min.
            for criterion in criteria:
                if criterion not in ('Max', 'Min'):
                    raise Exception(f'Critério deve ser Max ou Min.')
        else:
            raise Exception(f'Critérios não podem ser nulos.')
        return

    def set_criteria_description(self, criteria_description):
        if criteria_description is not None:
            except_raised = False
            data_struct = str(type(criteria_description))
            if  data_struct == "<class 'list'>":
                self.criteria_description = np.array(criteria_description)
            elif data_struct == "<class 'numpy.ndarray'>":
                self.criteria_description = criteria_description
            else:
                except_raised = True
                raise Exception(f'Estrutura de dados {data_struct} não é aceita.')

            if not except_raised and self.criteria_description.ndim != 1:
                raise Exception(f'Dimensão igual a 1 não é aceita.')
        else:
            raise Exception(f'Critérios não podem ser nulos.')
        return

    def set_alternatives_description(self, alternatives_description):
        if alternatives_description is not None:
            except_raised = False
            data_struct = str(type(alternatives_description))
            if  data_struct == "<class 'list'>":
                self.alternatives_description = np.array(alternatives_description)
            elif data_struct == "<class 'numpy.ndarray'>":
                self.alternatives_description = alternatives_description
            else:
                except_raised = True
                raise Exception(f'Estrutura de dados {data_struct} não é aceita.')

            if not except_raised and self.alternatives_description.ndim != 1:
                raise Exception(f'Dimensão igual a 1 não é aceita.')
        else:
            raise Exception(f'Critérios não podem ser nulos.')
        return

    def set_alternatives(self, alternatives):
        if alternatives is not None:
            except_raised = False
            data_struct = str(type(alternatives))
            if  data_struct == "<class 'list'>":
                self.alternatives = np.array(alternatives)
            elif data_struct == "<class 'numpy.ndarray'>":
                self.alternatives = alternatives
            else:
                except_raised = True
                raise Exception(f'Estrutura de dados {data_struct} não é aceita.')

            if not except_raised and self.alternatives.ndim != 2:
                raise Exception(f'Dimensão maior que 2 não é aceita.')
        else:
            raise Exception(f'Modelo não pode ser nulo.')
        return

    def set_W(self, W):
        if W is not None:
            except_raised = False
            data_struct = str(type(W))
            if  data_struct == "<class 'list'>":
                self.W = np.array(W)
            elif data_struct == "<class 'numpy.ndarray'>":
                self.W = W
            else:
                except_raised = True
                raise Exception(f'Estrutura de dados {data_struct} não é aceita.')

            if not except_raised and self.W.ndim > 1:
                raise Exception(f'Dimensão deve ser 1.')
        else:
            raise Exception(f'W não pode ser nulo.')
        return

    def normalize(self):
        # Normalize the criterion matrix values.
        normalized_alternatives = []
        col_len = len(self.alternatives[0])
        for col in range(col_len):
            col_sum = self.alternatives[:, col].sum()
            normalized_col = []
            for row in range(len(self.alternatives[:,col])):
                normalized_cel = round(self.alternatives[row,col] / col_sum, 4)
                normalized_col.append(normalized_cel)
            normalized_alternatives.append(normalized_col)
        self.normalized_alternatives = np.array(normalized_alternatives).transpose()

        # Calculate d Max.
        d = []
        for row in normalized_alternatives:
            d.append(max(row) - min(row))
        self.d_max = max(d)

        # Normalize the criterion matrix values.
        normalized_W = []
        w_sum = self.W.sum()
        for item in self.W:
            normalized_cel = round(item / w_sum, 4)
            normalized_W.append(normalized_cel)
        self.normalized_W = np.array(normalized_W)
        return

    def make_agreement_matrix(self):
        rows, cols = self.normalized_alternatives.shape
        alternatives_agreements = []
        dominances = []
        for alternative_a in range(rows):
            alternative_agreements = []
            alternative_dominance = []
            for alternative_b in range(rows):
                agreements = np.zeros(cols)
                dominance = True
                if alternative_a != alternative_b:
                    for col in range(cols):
                        if self.criteria[col] == 'Max':
                            if self.normalized_alternatives[alternative_a, col] >= self.normalized_alternatives[alternative_b, col]:
                                agreements[col] = self.normalized_W[col]
                            else:
                                dominance = False
                        elif self.criteria[col] == 'Min':
                            if self.normalized_alternatives[alternative_a, col] <= self.normalized_alternatives[alternative_b, col]:
                                agreements[col] = self.normalized_W[col]
                            else:
                                dominance = False
                alternative_dominance.append(dominance)
                alternative_agreements.append(agreements.sum())
            alternatives_agreements.append(alternative_agreements)
            dominances.append(alternative_dominance)
        self.agreement = np.array(alternatives_agreements)
        self.dominances = np.array(dominances)
        return

    def make_disagreement_matrix(self):
        rows, cols = self.normalized_alternatives.shape
        alternatives_disagreements = []
        for alternative_a in range(rows):
            alternative_disagreements = []
            for alternative_b in range(rows):
                diagreements = np.zeros(cols)
                if alternative_a != alternative_b:
                    for col in range(cols):
                        if self.criteria[col] == 'Max':
                            if self.normalized_alternatives[alternative_a, col] < self.normalized_alternatives[alternative_b, col]:
                                if not self.dominances[alternative_a, alternative_b]:
                                    diagreements[col] = self.normalized_alternatives[alternative_b, col] - self.normalized_alternatives[alternative_a, col]
                        elif self.criteria[col] == 'Min':
                            if self.normalized_alternatives[alternative_a, col] > self.normalized_alternatives[alternative_b, col]:
                                if not self.dominances[alternative_a, alternative_b]:
                                    diagreements[col] = self.normalized_alternatives[alternative_b, col] - self.normalized_alternatives[alternative_a, col]
                alternative_disagreements.append(diagreements.max() / self.d_max)
            alternatives_disagreements.append(alternative_disagreements)
        self.disagreement= np.array(alternatives_disagreements)
        return

    def make_superation_matrix(self):
        rows, cols = self.normalized_alternatives.shape
        cols = rows
        self.superation = np.zeros((rows, cols))
        for row in range(rows):
            for col in range(cols):
                if self.disagreement[row, col] < self.disagreement_threshold and self.agreement[row, col] > self.agreement_threshold:
                    self.superation[row, col] = 1
        return

    def make_recomendation(self):
        rows, cols = self.normalized_alternatives.shape
        cols = rows
        if self.alternatives_description is None:
            self.alternatives_description = ['alternative' + str(i) for i in range(rows)]
        elif len(self.alternatives_description) < rows:
            difference = rows - len(self.alternatives_description)
            self.alternatives_description += ['alternative' + str(i) for i in range(difference)]
        recomendations = [list(self.alternatives_description)]
        scores = []
        for col in range(cols):
            score = 'Selected' if self.superation[:, col].sum() == 0 else 'Not Selected'
            scores.append(score)
        recomendations.append(scores)
        self.recomendations = np.array(recomendations).transpose()
        return

    def exec(self):
        self.normalize()
        self.make_agreement_matrix()
        self.make_disagreement_matrix()
        self.make_superation_matrix()
        self.make_recomendation()
        self.mount_model()
        return