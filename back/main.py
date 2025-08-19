import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "tuto.api:app", host="0.0.0.0", port=18000, log_level="debug", reload=True
    )
