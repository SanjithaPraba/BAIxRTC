from database.connection_pool import ConnectionPool
from LangGraph.message_categorizer import MessageCategorizer
from pathlib import Path
import time

BATCH_SIZE = 10

def main():
    pool = ConnectionPool()
    conn = pool.get_connection()
    cur = conn.cursor()
    categorizer = MessageCategorizer(Path("../database/categories.json"))

    while True:
        # Pull a batch of uncategorized messages
        cur.execute("SELECT id, message FROM threads WHERE category IS NULL LIMIT %s;", (BATCH_SIZE,))
        rows = cur.fetchall()

        if not rows:
            print("All messages classified.")
            break

        ids = [row[0] for row in rows]
        texts = [row[1] for row in rows]

        try:
            categories = categorizer.classify_batch(texts)
        except Exception as e:
            print(f"Error during batch classification: {e}")
            break

        # Update each message with its predicted category
        for msg_id, category in zip(ids, categories):
            cur.execute("UPDATE threads SET category = %s WHERE id = %s;", (category, msg_id))

        conn.commit()
        print(f"Updated {len(categories)} messages")

        # pausing 5 sec to respect rate limits
        time.sleep(5)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
