sudo pip3 install -r requirements.txt
sudo cp agents_libre.conf /etc/supervisor/conf.d/
sudo cp agents_libre_nginx.conf /etc/nginx/sites-enabled/
sudo supervisorctl update
sudo systemctl restart nginx
sudo certbot --nginx -d libre.medsenger.ru
touch config.py