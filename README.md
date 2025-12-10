# 🛒 Simple E-Commerce Store with AI Recommendation System (Apriori Algorithm)

A modern, scalable e-commerce platform built with **Django**, featuring user authentication, product management, cart & orders, and an intelligent **product recommendation system using the Apriori algorithm**.

The recommendation system analyzes **wishlist items**, **cart items**, and **past user transactions** to generate intelligent product suggestions.

---

## ✨ Features

### 🛍️ E-Commerce Features

* User registration & login
* Product listing with categories
* Product detail page
* Add to cart
* Wishlist system
* Checkout & order processing
* User dashboard

### 🤖 AI Recommendation System

* Uses **Apriori Algorithm** for association rule mining
* Uses **past purchase history**, **wishlist**, and **cart** as transaction dataset
* Calculates:

  * frequent itemsets
  * support
  * confidence
  * lift values
* Suggests products with the highest association relevance
* Modular design for easy upgrade (FP-Growth, ML models, etc.)

## 🏗️ System Architecture

### **1. Client Layer**

* Browser
* Mobile browsers

### **2. Presentation Layer (Frontend)**

* HTML, CSS
* JavaScript
* Django Templates

### **3. Application Layer (Backend)**

* Django Views & DRF API
* Authentication module
* Recommendation module
* Cart & order service controllers

### **4. AI/Recommendation Engine**

* Apriori algorithm (mlxtend)
* Transaction builder
* Rule generator
* Recommendation selector

### **5. Database Layer**

* SQLite
* Tables:

  * Users
  * Products
  * Orders
  * OrderItems
  * Wishlist
  * Cart

### **6. Optional Extensions**

* Redis caching
* Celery background tasks
* Cloud file storage

---

## 🚀 Installation Guide

### 1️⃣ Create Virtual Environment

```bash
pip install virtualenv
virtualenv venv
```

### 2️⃣ Activate Environment

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

### 4️⃣ Run Migrations

```bash
python manage.py migrate
```

### 5️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

### 6️⃣ Start Server

```bash
python manage.py runserver
```

---

## 📈 Future Enhancements

* FP-Growth algorithm for faster mining
* Collaborative filtering
* Product vector embedding (deep learning)
* Real-time tracking recommendations
* Add Paystack / Flutterwave payments

