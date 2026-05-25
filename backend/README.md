---
title: Aspira Backend
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Aspira Backend

This is the backend API for Aspira, built with FastAPI and running in a Docker container on Hugging Face Spaces.

## Deployment to Hugging Face

To push only the backend folder to Hugging Face Spaces from the root of the repository:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git subtree push --prefix backend hf main
```
