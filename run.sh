while true; do
    echo "===== STARTING CRAWLER ====="

    PYTHONPATH=. ./venv/bin/python src/main.py --mode real --headless

    echo "===== CRAWLER FINISHED ====="

    git add data/ export/ .gitattributes

    git commit -m "Incremental Street View archival $(date)" || true

    git push origin main

    echo "===== SLEEPING ====="

    sleep 300
done