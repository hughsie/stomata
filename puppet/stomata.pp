file { '/var/www':
    ensure => 'directory',
}
vcsrepo { '/var/www/stomata':
    ensure => present,
    provider => git,
    revision => $git_revision,
    source => 'https://github.com/hughsie/stomata.git',
    user => 'nginx',
    group => 'nginx',
    require => [ File['/var/www'], Package['nginx']],
}
file { '/mnt/ipfs':
    ensure => 'directory',
    owner => 'nginx',
    group => 'nginx',
    require => [ Package['nginx'] ],
}
file { '/var/www/stomata/custom.cfg':
    ensure => 'file',
    owner => 'nginx',
    group => 'nginx',
    content => "# Managed by Puppet, DO NOT EDIT
import os
DEBUG = False
PROPAGATE_EXCEPTIONS = False
SECRET_KEY = '${stomata_secret_key}'
APP_NAME = 'stomata'
SECRET_KEY = '${stomata_secret_key}'
HOST_NAME = '${server_hostname}'
ADMIN_EMAIL = 'admin@${server_hostname}'
STOMATA_API_KEY = '${stomata_api_key}'
STOMATA_SECRET_API_KEY = '${stomata_secret_api_key}'
IP = '${server_ip}'
PORT = 80
SQLALCHEMY_DATABASE_URI = 'postgresql://${dbusername}:${dbpassword}@${dbserver}/stomata'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
SESSION_COOKIE_SECURE = ${using_ssl}
REMEMBER_COOKIE_SECURE = ${using_ssl}
",
    require => [ Package['nginx'], Vcsrepo['/var/www/stomata'] ],
}

# python deps are installed using requirements.txt where possible
package { 'git':
    ensure => installed,
}
package { 'python3-pip':
    ensure => installed,
}
package { 'python3-virtualenv':
    ensure => installed,
}
exec { 'virtualenv_create':
    command => '/usr/bin/virtualenv-3 /var/www/stomata/env',
    refreshonly => true,
    require => [ Package['python3-virtualenv'] ],
}
exec { 'pip_requirements_install':
    command => '/var/www/stomata/env/bin/pip3 install -r /var/www/stomata/requirements.txt',
    path => '/usr/bin',
    refreshonly => true,
    require => [ Vcsrepo['/var/www/stomata'], Package['python3-pip'], Exec['virtualenv_create'] ],
}

# required for the PKCS#7 support
package { 'gnutls-utils':
    ensure => installed,
}

# set up the database
package { 'postgresql-server':
  ensure => installed,
}
service { 'postgresql':
    ensure => 'running',
    enable => true,
    require => Package['postgresql-server'],
}

file { '/var/www/stomata/gunicorn.py':
    ensure => "file",
    owner => 'nginx',
    group => 'nginx',
    content => "# Managed by Puppet, DO NOT EDIT
chdir = '/var/www/stomata'
wsgi_app = 'stomata:app'
user = 'nginx'
group = 'nginx'
workers = 2
worker_class = 'eventlet'
timeout = 600
bind = '127.0.0.1:5000'
loglevel = 'info'
accesslog = '-'
x_forwarded_for_header = True
",
    require => Vcsrepo['/var/www/stomata'],
}

file { '/etc/systemd/system/gunicorn.service':
    ensure => "file",
    content => "# Managed by Puppet, DO NOT EDIT
[Unit]
Description=gunicorn
After=network.target
[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=/var/www/stomata
ExecStart=/bin/sh -c './env/bin/gunicorn --config gunicorn.py stomata:app'
[Install]
WantedBy=multi-user.target
",
    require => [ Exec['pip_requirements_install'] ],
}

service { 'gunicorn':
    ensure => 'running',
    enable => true,
    require => File['/etc/systemd/system/gunicorn.service'],
}

file { '/etc/systemd/system/ipfsdaemon.service':
    ensure => "file",
    content => "# Managed by Puppet, DO NOT EDIT
[Unit]
Description=ipfsdaemon
After=network.target
[Service]
Type=simple
User=nginx
Group=nginx
WorkingDirectory=/var/www/stomata
ExecStart=/bin/sh -c 'IPFS_PATH=/mnt/ipfs ./go-ipfs/ipfs daemon'
[Install]
WantedBy=multi-user.target
",
}
service { 'ipfsdaemon':
    ensure => 'running',
    enable => true,
    require => File['/etc/systemd/system/ipfsdaemon.service'],
}

# start nginx load balancer
package { 'nginx':
    ensure => installed,
}
file { '/etc/nginx/nginx.conf':
    ensure => "file",
    content => "# Managed by Puppet, DO NOT EDIT
worker_processes 1;
user nginx nginx;
error_log  /var/log/nginx/error.log warn;
pid /run/nginx.pid;
events {
  worker_connections 1024;
  accept_mutex off;
}
http {
  include mime.types;
  default_type application/octet-stream;
  access_log /var/log/nginx/access.log combined;
  sendfile on;
  server_names_hash_bucket_size 128;
  server {
    listen 443 ssl;
    client_max_body_size 1G;
    server_name ${server_hostname};
    keepalive_timeout 5;
    underscores_in_headers on;
    location / {
      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto \$scheme;
      proxy_set_header Host \$http_host;
      proxy_redirect off;
      proxy_pass_request_headers on;
      proxy_pass http://127.0.0.1:5000;
    }
    ssl_certificate /etc/letsencrypt/live/${server_hostname}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${server_hostname}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    include /etc/nginx/default.d/*.conf;
  }
}
",
    require => [ Package['nginx'], Vcsrepo['/var/www/stomata'] ],
}
service { 'nginx':
    ensure => 'running',
    enable => true,
    require => [ Package['nginx'], Vcsrepo['/var/www/stomata'] ],
}
