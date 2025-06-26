# test_setup.py - Fixed version
import sys
import os


def test_imports():
    """Test all required imports and basic functionality"""
    print("Testing imports...")

    try:
        # Test core dependencies
        import spacy

        print("✓ spaCy imported successfully")

        import fastapi

        print("✓ FastAPI imported successfully")

        import pydantic

        print("✓ Pydantic imported successfully")

        import uvicorn

        print("✓ Uvicorn imported successfully")

        # Test Pinecone (this might fail if not configured yet)
        try:
            import pinecone

            print("✓ Pinecone imported successfully")
        except ImportError as e:
            print(f"⚠ Pinecone import failed: {e}")
            print("  Try: pip install pinecone-client")

        # Test python-dotenv
        try:
            import dotenv

            print("✓ python-dotenv imported successfully")
        except ImportError:
            print("⚠ python-dotenv not found - install with: pip install python-dotenv")

        print("\n" + "=" * 50)
        print("Testing spaCy model...")

        # Test spaCy model
        try:
            nlp = spacy.load("en_core_web_md")
            doc = nlp("Hello world test")
            print(f"✓ spaCy model loaded successfully")
            print(f"  Model: en_core_web_md")
            print(f"  Vector dimensions: {len(doc.vector)}")
            print(f"  Sample vector (first 5 dims): {doc.vector[:5]}")
        except OSError:
            try:
                nlp = spacy.load("en_core_web_sm")
                doc = nlp("Hello world test")
                print(f"✓ spaCy model loaded (small version)")
                print(f"  Model: en_core_web_sm")
                print(f"  Vector dimensions: {len(doc.vector)}")
                print("  ⚠ Consider upgrading to en_core_web_md for better vectors")
            except OSError:
                print("✗ No spaCy model found!")
                print("  Run: python -m spacy download en_core_web_md")
                print("  Or: python -m spacy download en_core_web_sm")
                return False

        print("\n" + "=" * 50)
        print("✓ All core components working!")
        print("✓ Environment setup complete!")
        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure you've installed all requirements:")
        print("pip install -r requirements.txt")
        return False


def test_environment_file():
    """Check if .env file exists and has required variables"""
    print("\n" + "=" * 50)
    print("Checking environment configuration...")

    if os.path.exists(".env"):
        print("✓ .env file found")

        from dotenv import load_dotenv

        load_dotenv()

        required_vars = ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"⚠ Missing environment variables: {missing_vars}")
            print("  Make sure to set these in your .env file")
        else:
            print("✓ All required environment variables set")

    else:
        print("⚠ .env file not found")
        print("  Create .env file with your Pinecone credentials")


if __name__ == "__main__":
    print("Knowledge-Based Chatbot - Setup Test")
    print("=" * 50)

    success = test_imports()
    test_environment_file()

    if success:
        print("\n🎉 Setup test completed successfully!")
        print("You're ready to move to Phase 2!")
    else:
        print("\n❌ Setup test failed. Please fix the issues above.")
        sys.exit(1)
