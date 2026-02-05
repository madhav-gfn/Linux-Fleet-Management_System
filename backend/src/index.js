import express from 'express'
import cors from 'cors'
const app = express();
const PORT = 8000;

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({ status: "manager-up" });
});

app.listen(PORT, () => {
  console.log(`Fleet Manager running on port ${PORT}`);
});
