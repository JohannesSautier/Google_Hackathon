How to querry the code after it is running on the Google Cloud consol: 


curl -s localhost:8080/run \                                                                              
  -H "Content-Type: application/json" \
  -d '{
    "origin": "India",
    "destination": "US",
    "since_days": 7,
    "max_articles": 20,
    "use_llm": true
  }'





