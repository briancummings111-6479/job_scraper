import pandas as pd
import os
from datetime import datetime

data = {
    'job_title': ['Software Engineer', 'Data Scientist'],
    'company': ['Tech Corp', 'Data Inc'],
    'location': ['San Francisco, CA', 'New York, NY'],
    'pay': ['$150k', '$140k'],
    'job_type_extracted': ['Full-time', 'Full-time'],
    'shift_schedule': ['Day', 'Day'],
    'job_url': ['http://example.com/1', 'http://example.com/2'],
    'scraped_date': [datetime.now(), datetime.now()]
}

df = pd.DataFrame(data)
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, 'dummy_data.xlsx')
df.to_excel(output_file, index=False)
print(f"Created {output_file}")
