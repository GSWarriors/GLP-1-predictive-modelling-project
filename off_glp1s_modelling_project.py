#need to find the drugs from the audit data i have that are listed. might have to get data from diff audit
#definitely need medical data too
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re


def create_weight_resistant_condition_feature(df):
  #we need to check for whether we're looking at a weight resistant condition
  other_conditions_to_check = [
      'Hypothyroidism',
      'Cushing syndrome',
      'Depression',
      'Obstructive sleep apnea',
      'Osteoarthritis',
      'Chronic back pain'
  ]

  #fill the na fields
  dx = df['PrimaryDXDescription (SEGAL FIELD)'].fillna('').str.lower()
  #build safe regex pattern to for diff ways these conditions are represented.
  pattern = '|'.join(re.escape(c.lower()) for c in other_conditions_to_check)
  df['Is_Weight_Resistant_Condition'] = np.where(
      dx.str.contains(pattern, regex=True),
      'Y',
      'N'
  )
  count = (df['Is_Weight_Resistant_Condition'] == 'N').sum()
  print("the couht: " + str(count))
  print()
  #first need to normalize categories into buckets
  #instead- impute the broad family of codes potentially to see what to do with missing values for the condition (so that it makes sense)
  #print("the weight resistant condition: " + str(df[df['Is_Weight_Resistant_Condition'] == 'Y']))
  #print()

  #use the mapped condition class we have




def hierarchical_fill_dx_description(df, target_col, class_col="MappedConditionClass", condition_col="MappedConditionName"):

  df = df.copy()
  global_mode = df[target_col].dropna().mode()
  global_file = global_mode.iloc[0] if not global_mode.empty else "Unknown"

  missing_mask = df[target_col].isna()

  for idx in df[missing_mask].index:
    cond = df.at[idx, condition_col] if condition_col in df.columns else np.nan
    cls = df.at[idx, class_col] if class_col in df.columns else np.nan

  fill_value = None

  if pd.notna(cond):
    cond_mode = df.loc[
          (df[condition_col] == cond) & df[target_col].notna(),
          target_col
      ].mode()

  if not cond_mode.empty:
    fill_value = cond_mode.iloc[0]




  if fill_value is None and pd.notna(cls):
    class_mode = df.loc[
        (df[class_col] == cls) & df[target_col].notna(),
        target_col
    ].mode()

  if not class_mode.empty:
      fill_value = class_mode.iloc[0]

  if fill_value is None:
    fill_value = global_fill

  df.at[idx, target_col] = fill_value

  return df


#here is where we're filling the categorical cols
def fill_categorical_cols(df):

  df['PrimaryDXDescription (SEGAL FIELD)'] = (
      df['PrimaryDXDescription (SEGAL FIELD)']
      .fillna(df['MappedConditionName'])
  )

  df['SecondaryDXDescription (SEGAL FIELD)'] = (
      df['SecondaryDXDescription (SEGAL FIELD)']
      .fillna(df['MappedConditionName'])
  )

  df['TertiaryDXDescription (SEGAL FIELD)'] = (
      df['TertiaryDXDescription (SEGAL FIELD)']
      .fillna(df['MappedConditionName'])
  )

  df['FourthDXDescription (SEGAL FIELD)'] = (
      df['FourthDXDescription (SEGAL FIELD)']
      .fillna(df['MappedConditionName'])
  )
  return df



"""creating a flag for whether or not someone has gotten chronic weight gain."""
def create_chronic_weight_flag(df):

    pharmacy_df = pd.DataFrame(df, columns=[
      "patient_id", "claim_reference_number", "product_name", "days_supply",
      "label_name", "age", "date_of_service", "BMI"
    ])

    #check if these are actually weight gain drugs and if there are more
    #load in the above dataframes into the dataset
    psychiatric_wt_gain = ["olanzapine", "quetiapine", "risperidone"]
    metabolic_wt_gain = ["insulin", "glipizide", "glyburide"]

    #cardiovascular weight gain drugs
    cardiovascular_weight_gain_drugs = {
        "metropolol",
        "atenolol",
        "propanolol"
    }

    glp1_drugs = {
        "semaglutide",
        "liraglutide",
        "dulaglutide",
        "tirzepatide"
    }

    pharmacy_df["label_name_clean"] = (
        pharmacy_df["label_name"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    pharmacy_df["psychiatric_weight_gain_flag"] = pharmacy_df["label_name_clean"].isin(psychiatric_wt_gain)
    pharmacy_df["metabolic_weight_gain_flag"] = pharmacy_df["label_name_clean"].isin(metabolic_wt_gain)
    pharmacy_df["cardiovascular_weight_gain_flag"] = pharmacy_df["label_name_clean"].isin(cardiovascular_weight_gain_drugs)



    #chronic weight gain flag creation- this is the second feature we're creating
    #it takes into account whether a drug is psychiatric weight gain, metabolic, or cardiovascular

    pharmacy_df["chronic_weight_gain_drug_flag"] = (
          pharmacy_df["psychiatric_weight_gain_flag"]
          | pharmacy_df["metabolic_weight_gain_flag"]
          | pharmacy_df["cardiovascular_weight_gain_flag"]
    )


    #map the flag to a 'Y' or 'N' flag value as a feature so we can see where the flag is
    pharmacy_df["chronic_weight_gain_drug_flag"] = np.where(
        pharmacy_df["chronic_weight_gain_drug_flag"],
        "Y",
        "N"
    )


    chronic_weight_rows = pharmacy_df[pharmacy_df["chronic_weight_gain_drug_flag"] == 'Y']
    #("the chronic weight rows: " + str(chronic_weight_rows))
    #print()


    #find rate at which being prescribed these drugs
    establish_drug_rate(pharmacy_df, psychiatric_wt_gain, glp1_drugs)


#making this to establish the drug rate for weight gain with psychiatric drugs
def establish_drug_rate(pharmacy_df, psychiatric_wt_gain, glp1_drugs):

  """pharmacy_df["psychiatric_weight_gain_flag"] = pharmacy_df["label_name"].isin(psychiatric_wt_gain)
  pharmacy_df["glp1_flag"] = pharmacy_df["label_name"].isin(glp1_drugs)

  #combined weight gain drug flag
  pharmacy_df["psychiatric_weight_gain_flag"] = pharmacy_df["psychiatric_weight_gain_flag"] #expand as needed
  patient_rate = pharmacy_df.groupby("claim_reference_number")["psychiatric_weight_gain_flag"].max().mean()
  pharmacy_df["glp1_flag"] = pharmacy_df["label_name_clean"].isin(glp1_drugs)
  pharmacy_df["overweight_flag"] = pharmacy_df["BMI"] >= 25
  pharmacy_df["obese_flag"] = pharmacy_df["BMI"] >= 30


  print(pharmacy_df["psychiatric_weight_gain_flag"].value_counts(dropna=False))
  print(pharmacy_df["glp1_flag"].value_counts(dropna=False))
  print(pharmacy_df["chronic_weight_gain_drug_flag"].value_counts(dropna=False))
  print()
  #first metric: rate of being prescribed one of
  #psychiatric, metabolic or cardiovascular weight gain drugs

  patient_level_flags = (
      pharmacy_df.groupby("patient_id")
      .agg(
          any_psych_weight_gain=("psychiatric_weight_gain_flag", "max"),
          any_metabolic_weight_gain=("metabolic_weight_gain_flag", "max"),
          any_cardio_weight_gain=("cardiovascular_weight_gain_flag", "max"),
          any_chronic_weight_gain=("chronic_weight_gain_drug_flag", "max"),
          any_glp1=("glp1_flag", "max")
      )
      .reset_index()
  )

  print("the rate at which being prescribed drugs: " + str(patient_level_flags))
  print()"""

  pharmacy_df = pharmacy_df.copy()
  pharmacy_df["label_name_clean"] = (
      pharmacy_df["label_name"] 
      .astype(str)
      .str.strip()
      .str.lower()
  )

  pharmacy_df["overweight_flag"] = pharmacy_df["BMI"] >= 25 
  pharmacy_df["obese_flag"] = pharmacy_df["BMI"] >= 30

  patient_level_flags = (
      pharmacy_df.groupby("patient_id")
      .agg(
          any_psych_weight_gain=("psychiatric_weight_gain_flag", "max"),
          any_metabolic_weight_gain=("metabolic_weight_gain_flag", "max"),
          any_cardio_weight_gain=("cardiovascular_weight_gain_flag", "max"),
          any_chronic_weight_gain=("chronic_weight_gain_drug_flag", "max"),
          #any_glp1=("glp1_flag", "max")
      )
      .reset_index()
  )

  print("the patient level flags: " + str(patient_level_flags))
  print()

  #the rates can be calculated by taking the mena amount
  psychiatric_wt_gain_rate = (
    pharmacy_df.groupby("patient_id")["psychiatric_weight_gain_flag"].max().mean()
  )

  #do the same thing to get the weight gain rates for the other drugs
  """psychiatric_wt_gain_rate = (
    pharmacy_df.groupby("patient_id")["psychiatric_weight_gain_flag"].max().mean()
  )
    psychiatric_wt_gain_rate = (
    pharmacy_df.groupby("patient_id")["psychiatric_weight_gain_flag"].max().mean()
  )
     psychiatric_wt_gain_rate = (
    pharmacy_df.groupby("patient_id")["psychiatric_weight_gain_flag"].max().mean()
  )"""
  
  print("The psychiatric weight gain rate: " + str(psychiatric_wt_gain_rate))
  print()

  """metabolic_wt_gain_rate = pharmacy_df[pharmacy_df['metabolic_weight_gain_flag'] == True].sum() / len(metabolic_wt_gain)
  cardiovascular_wt_gain_rate = pharmacy_df[pharmacy_df['cardiovascular_weight_gain_flag'] == True].sum() / len(cardiovascular_weight_gain_drugs)
  chronic_wt_gain_rate = pharmacy_df[pharmacy_df['chronic_weight_gain_drug_flag'] == True].sum() / len(glp1_drugs)

  print("the psychiatric weight gain rate: " + str(psychiatric_wt_gain_rate))
  print()"""







def main():
    #issue fixed with column names
    df = pd.read_csv('glp1_patient_synthetic_dataset.csv', encoding="utf-8-sig")
    #conditions to search for
    conditions_to_check = ['Polycystic ovarian syndrome', 'diabetes', 'sleep apnea', 'mental health']

    #the columns to search
    dx_columns = ['PrimaryDXDescription (SEGAL FIELD)',
        'SecondaryDXDescription (SEGAL FIELD)',
        'TertiaryDXDescription (SEGAL FIELD)',
        'FourthDXDescription (SEGAL FIELD)']

    pattern = '|'.join(conditions_to_check)

    #create boolean mask across all diagnosis columns
    mask = df[dx_columns].apply(
        lambda col: col.astype(str).str.contains(pattern, case=False, na=False, regex=True)
    ).any(axis=1)

    filtered_df = df[mask]


    #first handle the missing data fields.
    #impute mean data val for numeric fields
    #impute mode for categorical
    age_col = df['PatientAge (SEGAL FIELD)']

    #fill all na columns for patient age
    df['PatientAge (SEGAL FIELD)'] = df['PatientAge (SEGAL FIELD)'].fillna(df['PatientAge (SEGAL FIELD)'].mean())

    #now fill all null categorical cols as well

    total_null_values = df['PatientAge (SEGAL FIELD)'].isna().sum()

    df['PatientAge (SEGAL FIELD)'].plot(kind='hist', bins=20, title='Distribution of Column Name')
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.show()


    new_df = fill_categorical_cols(df)

    #now that we've handled all missing values/categorical, we can create the features we want
    create_weight_resistant_condition_feature(df)
    #check notes here on what aleyne said
    #now we need to add features based on pharmacy data and thresholds
    """print("the new dataframe: " + str(new_df['PrimaryDXDescription (SEGAL FIELD)'].isna().sum()))
    print("the new dataframe: " + str(new_df['SecondaryDXDescription (SEGAL FIELD)'].isna().sum()))
    print("the new dataframe: " + str(new_df['TertiaryDXDescription (SEGAL FIELD)'].isna().sum()))
    print("the new dataframe: " + str(new_df['FourthDXDescription (SEGAL FIELD)'].isna().sum()))
    print()"""
    #adding the pharmacy data we've generated
    pharmacy_df = pd.read_csv("pharmacy_data.csv")

    #create the chronic weight gain flag
    create_chronic_weight_flag(pharmacy_df)




main()
