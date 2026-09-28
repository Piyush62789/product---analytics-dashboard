"""
Data Generator for E-Commerce Product Analytics Dataset
Generates realistic user event streams with funnel progressions,
cohort retention behaviors, product interactions, and A/B test variants.
"""

import os
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_ecommerce_events(num_users=3500, start_date="2025-01-01", days=90, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    
    # Product Catalog definition
    catalog = [
        {"product_id": "PROD-101", "product_name": "Pro Wireless Noise-Canceling Headphones", "category": "Electronics", "price": 249.99},
        {"product_id": "PROD-102", "product_name": "Mechanical Gaming Keyboard RGB", "category": "Electronics", "price": 129.50},
        {"product_id": "PROD-103", "product_name": "Ultra HD 4K 27-inch Monitor", "category": "Electronics", "price": 389.00},
        {"product_id": "PROD-104", "product_name": "Ergonomic Vertical Wireless Mouse", "category": "Electronics", "price": 64.99},
        {"product_id": "PROD-105", "product_name": "Fast Wireless Charging Dock 3-in-1", "category": "Electronics", "price": 49.95},
        {"product_id": "PROD-201", "product_name": "Premium Merino Wool Sweater", "category": "Apparel", "price": 98.00},
        {"product_id": "PROD-202", "product_name": "Organic Heavyweight Cotton Hoodie", "category": "Apparel", "price": 75.00},
        {"product_id": "PROD-203", "product_name": "Waterproof Trail Running Jacket", "category": "Apparel", "price": 165.00},
        {"product_id": "PROD-204", "product_name": "Slim-Fit Stretch Denim Jeans", "category": "Apparel", "price": 85.00},
        {"product_id": "PROD-205", "product_name": "Athletic Breathable Performance Socks (3-Pack)", "category": "Apparel", "price": 24.50},
        {"product_id": "PROD-301", "product_name": "Double-Walled Pour-Over Kettle", "category": "Home & Living", "price": 68.00},
        {"product_id": "PROD-302", "product_name": "Ceramic Matte Dinnerware Set (16-pc)", "category": "Home & Living", "price": 140.00},
        {"product_id": "PROD-303", "product_name": "Linen Duvet Cover & Pillow Sham Set", "category": "Home & Living", "price": 185.00},
        {"product_id": "PROD-304", "product_name": "Smart LED Ambient Light Bar", "category": "Home & Living", "price": 54.99},
        {"product_id": "PROD-305", "product_name": "Aromatherapy Ultrasonic Essential Oil Diffuser", "category": "Home & Living", "price": 39.90},
        {"product_id": "PROD-401", "product_name": "Smart Fitness & Sleep Tracker Band", "category": "Fitness & Sports", "price": 119.00},
        {"product_id": "PROD-402", "product_name": "Adjustable Dumbbell Set (5-52.5 lbs)", "category": "Fitness & Sports", "price": 349.00},
        {"product_id": "PROD-403", "product_name": "Non-Slip Eco Rubber Yoga Mat (6mm)", "category": "Fitness & Sports", "price": 58.00},
        {"product_id": "PROD-404", "product_name": "Insulated Stainless Steel Hydration Bottle 32oz", "category": "Fitness & Sports", "price": 34.00},
        {"product_id": "PROD-501", "product_name": "Botanical Hydrating Facial Serum", "category": "Beauty & Wellness", "price": 45.00},
        {"product_id": "PROD-502", "product_name": "Exfoliating Mineral Body Scrub", "category": "Beauty & Wellness", "price": 28.50},
        {"product_id": "PROD-503", "product_name": "Restorative Night Eye Cream with Peptides", "category": "Beauty & Wellness", "price": 52.00},
    ]

    devices = ["Desktop", "Mobile", "Tablet"]
    device_weights = [0.42, 0.48, 0.10]

    traffic_sources = ["Organic Search", "Paid Search", "Social Media", "Email Campaign", "Direct", "Referral"]
    traffic_weights = [0.30, 0.25, 0.18, 0.12, 0.10, 0.05]

    countries = ["United States", "United Kingdom", "Germany", "Canada", "France", "Japan", "Australia"]
    country_weights = [0.45, 0.18, 0.12, 0.10, 0.07, 0.05, 0.03]

    users = []
    events = []

    # Assign persistent attributes to users
    for i in range(1, num_users + 1):
        user_id = f"USR-{i:05d}"
        # Cohort signup date
        signup_offset = random.randint(0, days - 1)
        signup_date = start_dt + timedelta(days=signup_offset)
        preferred_device = np.random.choice(devices, p=device_weights)
        preferred_source = np.random.choice(traffic_sources, p=traffic_weights)
        country = np.random.choice(countries, p=country_weights)
        
        # User Segment assignment
        seg_rand = random.random()
        if seg_rand < 0.15:
            user_segment = "VIP"
            activity_rate = 0.45  # Higher frequency
        elif seg_rand < 0.60:
            user_segment = "Returning"
            activity_rate = 0.25
        else:
            user_segment = "New"
            activity_rate = 0.10

        # A/B test variant assignment (50/50 randomized)
        ab_variant = "Treatment" if random.random() < 0.50 else "Control"

        users.append({
            "user_id": user_id,
            "signup_date": signup_date,
            "preferred_device": preferred_device,
            "preferred_source": preferred_source,
            "country": country,
            "user_segment": user_segment,
            "ab_variant": ab_variant,
            "activity_rate": activity_rate
        })

    # Generate sessions and events
    event_counter = 1
    session_counter = 1

    for user in users:
        signup_dt = user["signup_date"]
        days_remaining = (start_dt + timedelta(days=days) - signup_dt).days
        if days_remaining <= 0:
            days_remaining = 1

        # Determine number of sessions for this user over time
        num_sessions = max(1, np.random.poisson(lam=user["activity_rate"] * (days_remaining / 7) * 2))
        
        # Space sessions across their active days to simulate retention
        session_days = sorted(random.sample(range(days_remaining), min(num_sessions, days_remaining)))

        for s_day in session_days:
            session_id = f"SES-{session_counter:06d}"
            session_counter += 1
            
            session_date = signup_dt + timedelta(
                days=s_day, 
                hours=random.randint(8, 22), 
                minutes=random.randint(0, 59), 
                seconds=random.randint(0, 59)
            )

            # Device variations with 85% stickiness
            device = user["preferred_device"] if random.random() < 0.85 else np.random.choice(devices, p=device_weights)
            traffic = user["preferred_source"] if random.random() < 0.80 else np.random.choice(traffic_sources, p=traffic_weights)

            curr_time = session_date

            # Step 1: Page View (Landing / Home)
            events.append({
                "event_id": f"EVT-{event_counter:07d}",
                "user_id": user["user_id"],
                "session_id": session_id,
                "event_timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "page_view",
                "page_url": "/home",
                "product_id": None,
                "product_name": None,
                "category": None,
                "price": 0.0,
                "quantity": 0,
                "revenue": 0.0,
                "device": device,
                "traffic_source": traffic,
                "user_segment": user["user_segment"],
                "ab_variant": user["ab_variant"],
                "country": user["country"]
            })
            event_counter += 1

            # Determine progression through funnel
            # Base conversion probabilities
            view_prob = 0.72
            # Mobile has slightly higher bounce rate
            if device == "Mobile":
                view_prob -= 0.06
            if user["user_segment"] == "VIP":
                view_prob += 0.12

            if random.random() > view_prob:
                continue  # Bounced after homepage

            # Step 2: Product View(s)
            num_products_viewed = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.15, 0.05])[0]
            selected_products = random.sample(catalog, num_products_viewed)
            
            carted_product = None
            for prod in selected_products:
                curr_time += timedelta(seconds=random.randint(15, 120))
                events.append({
                    "event_id": f"EVT-{event_counter:07d}",
                    "user_id": user["user_id"],
                    "session_id": session_id,
                    "event_timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event_type": "product_view",
                    "page_url": f"/product/{prod['product_id'].lower()}",
                    "product_id": prod["product_id"],
                    "product_name": prod["product_name"],
                    "category": prod["category"],
                    "price": prod["price"],
                    "quantity": 1,
                    "revenue": 0.0,
                    "device": device,
                    "traffic_source": traffic,
                    "user_segment": user["user_segment"],
                    "ab_variant": user["ab_variant"],
                    "country": user["country"]
                })
                event_counter += 1

                # Step 2b: Wishlist interaction (micro-conversion)
                if random.random() < 0.10:
                    events.append({
                        "event_id": f"EVT-{event_counter:07d}",
                        "user_id": user["user_id"],
                        "session_id": session_id,
                        "event_timestamp": (curr_time + timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S"),
                        "event_type": "add_to_wishlist",
                        "page_url": f"/product/{prod['product_id'].lower()}",
                        "product_id": prod["product_id"],
                        "product_name": prod["product_name"],
                        "category": prod["category"],
                        "price": prod["price"],
                        "quantity": 1,
                        "revenue": 0.0,
                        "device": device,
                        "traffic_source": traffic,
                        "user_segment": user["user_segment"],
                        "ab_variant": user["ab_variant"],
                        "country": user["country"]
                    })
                    event_counter += 1

                if carted_product is None and random.random() < 0.28:
                    carted_product = prod

            if not carted_product:
                continue

            # Step 3: Add to Cart
            curr_time += timedelta(seconds=random.randint(10, 60))
            cart_qty = random.choices([1, 2, 3], weights=[0.82, 0.14, 0.04])[0]
            events.append({
                "event_id": f"EVT-{event_counter:07d}",
                "user_id": user["user_id"],
                "session_id": session_id,
                "event_timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "add_to_cart",
                "page_url": "/cart",
                "product_id": carted_product["product_id"],
                "product_name": carted_product["product_name"],
                "category": carted_product["category"],
                "price": carted_product["price"],
                "quantity": cart_qty,
                "revenue": 0.0,
                "device": device,
                "traffic_source": traffic,
                "user_segment": user["user_segment"],
                "ab_variant": user["ab_variant"],
                "country": user["country"]
            })
            event_counter += 1

            # Step 4: Initiate Checkout
            checkout_prob = 0.58
            if device == "Mobile":
                checkout_prob -= 0.05
            if user["user_segment"] == "VIP":
                checkout_prob += 0.15

            if random.random() > checkout_prob:
                continue

            curr_time += timedelta(seconds=random.randint(20, 180))
            events.append({
                "event_id": f"EVT-{event_counter:07d}",
                "user_id": user["user_id"],
                "session_id": session_id,
                "event_timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "initiate_checkout",
                "page_url": "/checkout",
                "product_id": carted_product["product_id"],
                "product_name": carted_product["product_name"],
                "category": carted_product["category"],
                "price": carted_product["price"],
                "quantity": cart_qty,
                "revenue": 0.0,
                "device": device,
                "traffic_source": traffic,
                "user_segment": user["user_segment"],
                "ab_variant": user["ab_variant"],
                "country": user["country"]
            })
            event_counter += 1

            # Step 5: Purchase
            # Treatment variant has a 1-click streamlined checkout (+7.5% relative lift)
            base_purchase_prob = 0.68
            if user["ab_variant"] == "Treatment":
                base_purchase_prob += 0.065  # Clear statistically significant lift
            if device == "Mobile":
                base_purchase_prob -= 0.04
            if user["user_segment"] == "VIP":
                base_purchase_prob += 0.12

            if random.random() > base_purchase_prob:
                continue

            curr_time += timedelta(seconds=random.randint(25, 240))
            order_revenue = round(carted_product["price"] * cart_qty, 2)
            events.append({
                "event_id": f"EVT-{event_counter:07d}",
                "user_id": user["user_id"],
                "session_id": session_id,
                "event_timestamp": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "purchase",
                "page_url": "/checkout/confirmation",
                "product_id": carted_product["product_id"],
                "product_name": carted_product["product_name"],
                "category": carted_product["category"],
                "price": carted_product["price"],
                "quantity": cart_qty,
                "revenue": order_revenue,
                "device": device,
                "traffic_source": traffic,
                "user_segment": user["user_segment"],
                "ab_variant": user["ab_variant"],
                "country": user["country"]
            })
            event_counter += 1

    df = pd.DataFrame(events)
    # Sort chronologically
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
    df = df.sort_values(by="event_timestamp").reset_index(drop=True)
    
    return df

if __name__ == "__main__":
    os.makedirs("d:/product/data", exist_ok=True)
    output_path = "d:/product/data/ecommerce_events.csv"
    print("Generating e-commerce event stream dataset...")
    df = generate_ecommerce_events(num_users=3800, start_date="2025-01-01", days=90, seed=42)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {len(df):,} events across {df['user_id'].nunique():,} unique users.")
    print(f"Saved dataset to {output_path}")
    print("Event distribution:")
    print(df['event_type'].value_counts())
