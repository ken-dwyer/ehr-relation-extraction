from typing import List, Tuple, Callable

import os
import sys
from pickle import dump, load
from IPython.core.display import display, HTML
from ehr import HealthRecord
import random

TPL_HTML = '<span style = "background-color: {color}; border-radius: 5px;">&nbsp;{content}&nbsp;</span>'

COLORS = {"Drug": "#aa9cfc", "Strength": "#ff9561", 
          "Form": "#7aecec", "Frequency": "#9cc9cc", 
          "Route": "#ffeb80", "Dosage": "#bfe1d9", 
          "Reason": "#e4e7d2", "ADE": "#ff8197", 
          "Duration": "#97c4f5"}

def display_ehr(text, entities):    
    '''
    Highlights EHR records with colors and displays
    them as HTML. Ideal for working with Jupyter Notebooks

    Parameters
    ----------
    text : str
        EHR record to render
    entities : dictionary / list
         A list of Entity objects

    Returns
    -------
    None.

    '''
    if isinstance(entities, dict):
        entities = list(entities.values())
    
    # Sort entity by starting range
    entities.sort(key = lambda ent: ent.range[0])

    # Final text to render
    render_text = ""
    start_idx = 0
    
    # Display legend
    for ent, col in COLORS.items():
        render_text += TPL_HTML.format(content = ent, color = col)
        render_text += "&nbsp" * 5
    
    render_text += '\n'
    render_text += '--' * 50
    render_text += "\n\n"
    
    # Replace each character range with HTML span template
    for ent in entities:
        render_text += text[start_idx:ent.range[0]]
        render_text += TPL_HTML.format(content = text[ent.range[0]:ent.range[1]], color = COLORS[ent.name])
        start_idx = ent.range[1]
    
    render_text += text[start_idx:]
    render_text = render_text.replace("\n", "<br>")
    
    # Render HTML
    display(HTML(render_text))


def read_data(data_dir: str = 'data/', train_ratio: int = 0.8, 
              tokenizer: Callable[[str], List[str]] = None, 
              verbose: int = 0) -> Tuple[List[HealthRecord], List[HealthRecord]]:
    '''
    Reads train and test data

    Parameters
    ----------
    data_dir : str, optional
        Directory where the data is located. The default is 'data/'.
    
    train_ratio : int, optional
        Percentage split of train data. The default is 0.8.
        
    tokenizer : Callable[[str], List[str]], optional
        The tokenizer function to use.. The default is None.
        
    verbose : int, optional
        1 to print reading progress, 0 otherwise. The default is 0.

    Returns
    -------
    Tuple[List[HealthRecord], List[HealthRecord]]
        Train data, Test data.

    '''
    # Get all the IDs of data
    file_ids = sorted(list(set(['.'.join(fname.split('.')[:-1])\
                                for fname in os.listdir(data_dir)\
                                    if not fname.startswith('.')])))
    
    # Splitting IDs into random training and test data
    random.seed(0)
    random.shuffle(file_ids)
    
    split_idx = int(train_ratio * len(file_ids)) 
    train_ids = file_ids[:split_idx]
    test_ids = file_ids[split_idx:]
    
    if verbose == 1:
        print("Train data:")
        
    train_data = []
    for idx, fid in enumerate(train_ids):
        record = HealthRecord(fid, text_path = data_dir + fid + '.txt', 
                              ann_path = data_dir + fid + '.ann', 
                              tokenizer = tokenizer)
        train_data.append(record)
        if verbose == 1:
            drawProgressBar(idx + 1, split_idx)
    
    if verbose == 1:
        print('\n\nTest Data:')
        
    test_data = []
    for idx, fid in enumerate(test_ids):
        record = HealthRecord(fid, text_path = data_dir + fid + '.txt', 
                              ann_path = data_dir + fid + '.ann', 
                              tokenizer = tokenizer)
        test_data.append(record)
        if verbose == 1:
            drawProgressBar(idx + 1, len(file_ids) - split_idx)
        
    return (train_data, test_data)


def generate_input_files(ehr_records: List[HealthRecord], 
                         filename: str, max_len:int = 510, 
                         sep: str = ' '):
    '''
    Write EHR records to a file.

    Parameters
    ----------
    ehr_records : List[HealthRecord]
        List of EHR records.
    
    filename : str
        File name to write to.
    
    max_len : int, optional
        Max length of an example. The default is 510.
        
    sep : str, optional
        Token-label separator. The default is a space.

    '''
    with open(filename, 'w') as f:
      for record in ehr_records:
        
        split_idx = record.get_split_points(max_len = max_len)
        labels = record.get_labels()
        tokens = record.get_tokens()
  
        start = split_idx[0]
        end = split_idx[1]
  
        for i in range(1, len(split_idx)):
          for (token, label) in zip(tokens[start:end+1], labels[start:end+1]):
            f.write('{}{}{}\n'.format(token, sep, label))      
  
          start = end + 1
          if i != len(split_idx)-1:
            end = split_idx[i+1]
            f.write('\n')
  
        f.write('\n')
    print("Data successfully saved in " + filename)


def drawProgressBar(current, total, string = '', barLen = 20):
    '''
    Draws a progress bar, like [====>    ] 40%
    
    Parameters
    ------------
    current: int/float
             Current progress
    
    total: int/float
           The total from which the current progress is made
             
    string: str
            Additional details to write along with progress
    
    barLen: int
            Length of progress bar
    '''
    percent = current / total
    arrow = ">"
    if percent == 1:
        arrow = ""
    # Carriage return, returns to the begining of line to owerwrite
    sys.stdout.write("\r")
    sys.stdout.write("Progress: [{:<{}}] {}/{}".format("=" * int(barLen * percent) + arrow, 
                                                         barLen, current, total) + string)
    sys.stdout.flush()


def is_whitespace(char):
    '''
    Checks if the character is a whitespace
    
    Parameters
    --------------
    char: str
          A single character string to check
    '''
    # ord() returns unicode and 0x202F is the unicode for whitespace
    if char == " " or char == "\t" or char == "\r" or char == "\n" or ord(char) == 0x202F:
        return True
    else:
        return False


def is_punct(char):
    '''
    Checks if the character is a punctuation
    
    Parameters
    --------------
    char: str
          A single character string to check
    '''
    if char == "." or char == "," or char == "!" or char == "?" or char == '\\':
        return True
    else:
        return False
    

def save_pickle(file, variable):
    '''
    Saves variable as a pickle file
    
    Parameters
    -----------
    file: str
          File name/path in which the variable is to be stored
    
    variable: object
              The variable to be stored in a file
    '''
    if file.split('.')[-1] != "pkl":
        file += ".pkl"
        
    with open(file, 'wb') as f:
        dump(variable, f)
        print("Variable successfully saved in " + file)


def open_pickle(file):
    '''
    Returns the variable after reading it from a pickle file
    
    Parameters
    -----------
    file: str
          File name/path from which variable is to be loaded
    '''
    if file.split('.')[-1] != "pkl":
        file += ".pkl"
    
    with open(file, 'rb') as f:
        return load(f)