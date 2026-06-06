import asyncio
import edge_tts

async def main():
    text = "Hello! This is a simple test to inspect word boundary events."
    voice = "en-US-AndrewNeural"
    communicate = edge_tts.Communicate(text, voice)
    
    print("Starting stream...")
    word_count = 0
    audio_chunks = 0
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks += 1
        else:
            print(f"Received metadata chunk: {chunk}")
            if chunk["type"] == "WordBoundary":
                word_count += 1
                
    print(f"Finished. Audio chunks: {audio_chunks}, WordBoundary chunks: {word_count}")

if __name__ == "__main__":
    asyncio.run(main())
