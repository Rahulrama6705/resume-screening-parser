#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Resume Parser System${NC}"
echo -e "${BLUE}========================================${NC}"

# Activate virtual environment
source venv/bin/activate

# Check if Ollama is running
echo -e "\n${YELLOW}Checking Ollama...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Ollama...${NC}"
    nohup /opt/homebrew/bin/ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
fi

# Check if phi3:mini is available
echo -e "${YELLOW}Checking phi3:mini model...${NC}"
if ! curl -s http://localhost:11434/api/tags | grep -q "phi3:mini"; then
    echo -e "${YELLOW}Pulling phi3:mini model...${NC}"
    /opt/homebrew/bin/ollama pull phi3:mini
fi

echo -e "${GREEN}✓ Ollama ready${NC}"

# Menu
echo -e "\n${BLUE}Select option:${NC}"
echo "1) Run FastAPI server (port 8000)"
echo "2) Run Streamlit UI (port 8501)"
echo "3) Batch process resumes"
echo "4) Run both servers (FastAPI + Streamlit)"
echo "5) Exit"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo -e "\n${GREEN}Starting FastAPI server...${NC}"
        echo "API available at: http://localhost:8000"
        echo "Docs at: http://localhost:8000/docs"
        python3 main.py
        ;;
    2)
        echo -e "\n${GREEN}Starting Streamlit UI...${NC}"
        echo "UI available at: http://localhost:8501"
        streamlit run streamlit_app.py
        ;;
    3)
        echo -e "\n${GREEN}Starting batch processor...${NC}"
        read -p "Max resumes to process (0 for all): " max_resumes
        if [ "$max_resumes" -eq 0 ]; then
            python3 batch_processor.py
        else
            python3 batch_processor.py $max_resumes
        fi
        ;;
    4)
        echo -e "\n${GREEN}Starting both servers...${NC}"
        echo "FastAPI: http://localhost:8000"
        echo "Streamlit: http://localhost:8501"
        python3 main.py &
        sleep 2
        streamlit run streamlit_app.py
        ;;
    5)
        echo -e "${YELLOW}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
