FROM mysql:8.0-debian

# Install Python and required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    netcat-traditional \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages \
    Django==4.2.27 \
    mysqlclient

COPY ./local_setting/local_mysql/init.sql /docker-entrypoint-initdb.d/
COPY ./local_setting/local_mysql/conf.d /etc/mysql/conf.d
RUN chmod 644 /etc/mysql/conf.d/my.cnf

# Copy Django models and migration scripts
COPY ./local_setting/local_mysql /app/local_setting/local_mysql
COPY ./local_setting/__init__.py /app/local_setting/__init__.py

# Ensure migrations directory exists with proper permissions
RUN mkdir -p /app/local_setting/local_mysql/migrations && \
    chmod 755 /app/local_setting/local_mysql/migrations

# Copy and setup migration runner
COPY ./local_setting/local_mysql/run_migrations.py /docker-entrypoint-initdb.d/99-run-migrations.py
RUN chmod +x /docker-entrypoint-initdb.d/99-run-migrations.py

# Copy startup script
COPY ./local_setting/local_mysql/start_with_migrations.sh /usr/local/bin/start_with_migrations.sh
RUN chmod +x /usr/local/bin/start_with_migrations.sh

# Set custom entrypoint
ENTRYPOINT ["/usr/local/bin/start_with_migrations.sh"]

# Execute the migration script in the background when container starts
# Note: We cannot override ENTRYPOINT easily in mysql image, so we rely on 
# /docker-entrypoint-initdb.d/ scripts which run only on first initialization.
# For subsequent runs, we might need a different approach if we want migrations to run every time.

