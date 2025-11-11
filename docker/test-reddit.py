#!/usr/bin/env python3
"""
Final integration test: Reddit search with browser-use
Tests the complete agent workflow with real LLM and browser automation.
"""
from browser_use import Agent
from browser_use.llm import ChatOpenAI
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("=" * 70)
    print("  Final Reddit Test - Browser-Use Integration")
    print("=" * 70)
    print()
    
    print("🎯 Task: Go to Reddit, search for 'browser-use', click on the first post and return the first comment.")
    print()
    
    agent = Agent(
        task="Go to Reddit, search for 'browser-use', click on the first post and return the first comment.",
        llm=ChatOpenAI(model="gpt-5-mini"),
    )
    
    print("🚀 Starting agent...")
    result = await agent.run()
    
    print()
    print("=" * 70)
    print("  Test Results")
    print("=" * 70)
    print()
    print(f"Result: {result.final_result()}")
    print()
    print(f"Steps taken: {result.number_of_steps()}")
    print(f"Duration: {result.total_duration_seconds():.2f} seconds")
    print(f"Success: {result.is_successful()}")
    print()
    print("=" * 70)
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
