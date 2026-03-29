import openenv.core as oe
from email_env import EmailEnvironment, Action, Observation, Reward

# Since openenv seems to expect a server/app.py, we might simply need an entry point.
# I'll create a basic FastAPI app if needed, or stick to openenv abstractions.
# Frequently openenv has a builder or fastapi wrapper.
# If openenv requires server/app.py, this might be the place where we instantiate the env.
from fastapi import FastAPI
app = FastAPI(title="Email Triage OpenEnv")

env = EmailEnvironment()

@app.post("/step")
def step(action: Action):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

@app.post("/reset")
def reset(task_id: str = "task_1_easy_spam"):
    obs = env.reset(task_id)
    return {"observation": obs.model_dump()}

@app.get("/state")
def state():
    return env.state()

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
