"""Check Databento account details and available datasets"""
import databento as db
import os

api_key = os.getenv("DATABENTO_API_KEY")

print("=" * 70)
print("🔍 DATABENTO ACCOUNT CHECK")
print("=" * 70)
print(f"🔑 API Key: {api_key[:12]}***")
print()

try:
    # Create Historical client to check account
    client = db.Historical(key=api_key)
    
    print("✅ Client created successfully")
    print()
    
    # Check available datasets
    print("📊 Available Datasets:")
    print("-" * 70)
    
    datasets = client.metadata.list_datasets()
    for dataset in datasets:
        print(f"  • {dataset}")
    
    print()
    print("-" * 70)
    print(f"Total: {len(datasets)} datasets")
    
    # Check if GLBX.MDP3 is available
    if "GLBX.MDP3" in [str(d) for d in datasets]:
        print("\n✅ GLBX.MDP3 (CME Globex) is available!")
        
        # Get more info about GLBX.MDP3
        print("\n📋 GLBX.MDP3 Details:")
        
        # List available schemas
        try:
            schemas = client.metadata.list_schemas(dataset="GLBX.MDP3")
            print(f"  Available schemas: {schemas}")
        except Exception as e:
            print(f"  Could not list schemas: {e}")
    else:
        print("\n⚠️  GLBX.MDP3 NOT in your subscription")
        print("You need to subscribe at: https://databento.com")
    
    print()
    print("=" * 70)
    print("✅ Account check complete!")
    
except db.BentoError as e:
    print(f"❌ Databento Error: {e}")
    print("\n💡 This might mean:")
    print("  1. API key is invalid")
    print("  2. Account is not active")
    print("  3. Network connection issue")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
