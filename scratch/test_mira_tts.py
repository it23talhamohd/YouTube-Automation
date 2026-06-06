import asyncio
import edge_tts

async def main():
    text = (
        "OpenAI’s former tech genius is back, and she is building a massive new AI rival! "
        "Mira Murati, the brilliant mind who led engineering at OpenAI, is reportedly raising millions for a brand new AI startup. "
        "Her goal? To build proprietary AI models and products that could challenge OpenAI and Google head-on. "
        "This comes after her shocking departure from OpenAI, leaving fans wondering what secrets she took with her. "
        "Is she about to release something even bigger than ChatGPT, or is the AI market getting too crowded? "
        "Would you use an AI made by the creator of ChatGPT? Tell us below, and hit subscribe for daily tech updates!"
    )
    voice = "en-US-AndrewNeural"
    communicate = edge_tts.Communicate(text, voice)
    
    print("Starting stream...")
    word_count = 0
    sentence_count = 0
    audio_chunks = 0
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks += 1
        else:
            print(f"Received metadata chunk: {chunk}")
            if chunk["type"] == "WordBoundary":
                word_count += 1
            elif chunk["type"] == "SentenceBoundary":
                sentence_count += 1
                
    print(f"Finished. Audio chunks: {audio_chunks}, SentenceBoundary chunks: {sentence_count}, WordBoundary chunks: {word_count}")

if __name__ == "__main__":
    asyncio.run(main())
