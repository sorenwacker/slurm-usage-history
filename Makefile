serve:
	nohup gunicorn -w 1 -b 0.0.0.0:8080 wsgi-saml:app &

getdata:
	rsync -avz --progress --delete --exclude=".*" daic:/tudelft.net/staff-umbrella/reit/slurm-usage-history/ /data/slurm-usage-history

devel:
	uv run slushi-dashboard --debug

gettestdata:
	rsync -avz --progress --delete --exclude=".*" --include="*/" --include="**/*2025*" --exclude="*" daic:/tudelft.net/staff-umbrella/reit/slurm-usage-history/ ./data/

