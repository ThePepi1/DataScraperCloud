#!/bin/bash
set -e

DB_PASSWORD="${db_password}"
SECRET_KEY="${superset_secret_key}"
ADMIN_PASSWORD="${superset_admin_password}"
ADMIN_USERNAME="${superset_admin_username}"
ADMIN_FIRSTNAME="${superset_admin_firstname}"
ADMIN_LASTNAME="${superset_admin_lastname}"
ADMIN_EMAIL="${superset_admin_email}"
VPC_CIDR="${vpc_cidr}"

# Update i instalacija
apt-get update -y
apt-get install -y postgresql postgresql-contrib python3-pip python3-venv libpq-dev
# PostgreSQL setup
sudo -u postgres psql -c "CREATE USER superset WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE superset_db OWNER superset;"
sudo -u postgres psql -c "CREATE DATABASE gold_db OWNER superset;"

# PostgreSQL da slusa unutar VPC
echo "listen_addresses = '*'" >> /etc/postgresql/*/main/postgresql.conf
echo "host all all $VPC_CIDR md5" >> /etc/postgresql/*/main/pg_hba.conf
systemctl restart postgresql
/opt/superset/bin/pip install cachetools

# Superset install
python3 -m venv /opt/superset
/opt/superset/bin/pip install --upgrade pip
/opt/superset/bin/pip install apache-superset psycopg2-binary

# Superset init
export SUPERSET_SECRET_KEY="$SECRET_KEY"
export SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://superset:$DB_PASSWORD@localhost/superset_db"

/opt/superset/bin/superset db upgrade
/opt/superset/bin/superset fab create-admin \
  --username "$ADMIN_USERNAME" \
  --firstname "$ADMIN_FIRSTNAME" \
  --lastname "$ADMIN_LASTNAME" \
  --email "$ADMIN_EMAIL" \
  --password "$ADMIN_PASSWORD"
/opt/superset/bin/superset init

# Superset systemd servis
cat > /etc/systemd/system/superset.service <<SERVICE
[Unit]
Description=Apache Superset
After=network.target postgresql.service

[Service]
Environment="SUPERSET_SECRET_KEY=$SECRET_KEY"
Environment="SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://superset:$DB_PASSWORD@localhost/superset_db"
ExecStart=/opt/superset/bin/superset run -h 0.0.0.0 -p 8088 --with-threads
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable superset
systemctl start superset
sudo /opt/superset/bin/pip install cachetools
sudo systemctl restart superset