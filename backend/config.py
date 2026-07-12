import os
from dotenv import load_dotenv

load_dotenv()

# Timezone used to bucket XP / activity charts by calendar day. The audience is Indian
# (Spoken Tutorial), so a day runs midnight-to-midnight IST unless overridden via env.
# Changing this one value re-buckets every daily chart.
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
