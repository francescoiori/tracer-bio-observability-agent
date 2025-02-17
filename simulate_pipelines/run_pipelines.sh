# Start pipelines after monitoring begins
echo "Starting parallel pipeline execution"
chmod +x pipeline_1.sh pipeline_2.sh

for j in {1..5}; do
  for i in {1..2}; do
      ./pipeline_1.sh &
      ./pipeline_2.sh &
      sleep 5
  done
  wait
done

./bioinformatics_pipeline.sh

wait
echo "Parallel execution complete"