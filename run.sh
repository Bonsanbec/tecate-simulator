while true; do
    echo "===== STARTING CRAWLER ====="

    PYTHONPATH=. ./venv/bin/python src/main.py --headless

    echo "===== CRAWLER FINISHED ====="

    git add data/ export/ tecate_reconstruction.blend *.glb .gitattributes

    git commit -m "Incremental Street View archival $(date)" || true

    git push origin master

    echo "===== SLEEPING ====="

    sleep 30
done