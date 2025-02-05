import pandas as pd
import os
import re

BASE_DIR = "Charts_World"
OUTPUT_DIR = "Charts_no_info"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def extract_country_info(folder_name):
    match = re.match(r"Charts_([A-Z]+)([\U0001F1E6-\U0001F1FF]+)", folder_name)
    if match:
        return match.group(1), match.group(2)
    return folder_name, "🌍"

def extract_week_date(filename):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    return match.group(1) if match else None

def extract_track_id(uri):
    return uri.split(':')[-1] if pd.notnull(uri) else None

def list_csv_files(folder_path):
    all_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
    all_files.sort(reverse=True, key=lambda x: extract_week_date(x))
    return all_files

def process_file(file_path, country_code):
    df = pd.read_csv(file_path)

    # 🔹 On garde uniquement les 50 premières places
    df = df[df['rank'] <= 50]

    df = df[['rank', 'uri', 'artist_names', 'track_name', 'source', 'streams', 'peak_rank', 'previous_rank', 'weeks_on_chart']]
    df['country'] = country_code
    df['week_date'] = extract_week_date(file_path)
    df['track_id'] = df['uri'].apply(extract_track_id)
    return df

def merge_csv_files_from_folder(folder_path, country_code):
    all_files = list_csv_files(folder_path)
    df_list = [process_file(os.path.join(folder_path, file), country_code) for file in all_files]
    return pd.concat(df_list, ignore_index=True)

def merge_all_countries(base_folder):
    all_data = []
    country_info_list = []

    for continent in os.listdir(base_folder):
        continent_path = os.path.join(base_folder, continent)
        if os.path.isdir(continent_path):
            print(f"📂 Traitement du continent : {continent}")

            for country_folder in os.listdir(continent_path):
                country_path = os.path.join(continent_path, country_folder)

                if os.path.isdir(country_path):
                    print(f"    🌍 Fusion des fichiers pour : {country_folder}")

                    country_code, flag = extract_country_info(country_folder)
                    merged_data = merge_csv_files_from_folder(country_path, country_code)

                    all_data.append((merged_data, continent, country_code, flag))

    final_df = pd.concat([data[0] for data in all_data], ignore_index=True)
    return final_df, all_data

def clean_data(df):
    df['week_date'] = pd.to_datetime(df['week_date'], format='%Y-%m-%d')
    df.sort_values(by=['week_date', 'rank'], ascending=[False, True], inplace=True)
    df.drop(columns=['previous_rank'], errors='ignore', inplace=True)
    return df

def save_merged_data(df, all_data):
    for merged_data, continent, country_code, flag in all_data:
        continent_folder = os.path.join(OUTPUT_DIR, continent)
        if not os.path.exists(continent_folder):
            os.makedirs(continent_folder)

        output_file = os.path.join(continent_folder, f"charts_{country_code}{flag}.csv")

        country_df = df[df['country'] == country_code]
        country_df.to_csv(output_file, index=False)
        print(f"✅ Fichier {output_file} créé avec succès !")

if __name__ == "__main__":
    merged_data, all_data = merge_all_countries(BASE_DIR)
    cleaned_data = clean_data(merged_data)
    save_merged_data(cleaned_data, all_data)
