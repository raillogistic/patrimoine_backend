--
-- PostgreSQL database dump
--

-- Dumped from database version 12.3 (Ubuntu 12.3-1.pgdg18.04+1)
-- Dumped by pg_dump version 12.22 (Ubuntu 12.22-0ubuntu0.20.04.2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: billing_fichefacturation; Type: TABLE; Schema: public; Owner: mkhaled
--

CREATE TABLE public.billing_fichefacturation (
    date date,
    id bigint NOT NULL,
    created_at timestamp with time zone,
    numero integer,
    state character varying(100),
    canceled boolean,
    client_id bigint NOT NULL,
    owner_id integer,
    bon_commands character varying(200),
    ht double precision,
    debours double precision,
    observation text,
    tva double precision,
    date_attachement date
);


ALTER TABLE public.billing_fichefacturation OWNER TO mkhaled;

--
-- Name: billing_fichefacturation_id_seq; Type: SEQUENCE; Schema: public; Owner: mkhaled
--

CREATE SEQUENCE public.billing_fichefacturation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.billing_fichefacturation_id_seq OWNER TO mkhaled;

--
-- Name: billing_fichefacturation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkhaled
--

ALTER SEQUENCE public.billing_fichefacturation_id_seq OWNED BY public.billing_fichefacturation.id;


--
-- Name: billing_ficheitem; Type: TABLE; Schema: public; Owner: mkhaled
--

CREATE TABLE public.billing_ficheitem (
    id bigint NOT NULL,
    designation character varying(300) NOT NULL,
    unit character varying(50),
    quantity double precision NOT NULL,
    price_u double precision NOT NULL,
    price double precision,
    dossier_id bigint,
    fich_id bigint,
    quantity_unit character varying(50),
    bon_command character varying(100),
    remarque text,
    verified boolean,
    created_at timestamp with time zone,
    "order" integer,
    observation text,
    canceled boolean
);


ALTER TABLE public.billing_ficheitem OWNER TO mkhaled;

--
-- Name: billing_ficheitem_id_seq; Type: SEQUENCE; Schema: public; Owner: mkhaled
--

CREATE SEQUENCE public.billing_ficheitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.billing_ficheitem_id_seq OWNER TO mkhaled;

--
-- Name: billing_ficheitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mkhaled
--

ALTER SEQUENCE public.billing_ficheitem_id_seq OWNED BY public.billing_ficheitem.id;


--
-- Name: billing_fichefacturation id; Type: DEFAULT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_fichefacturation ALTER COLUMN id SET DEFAULT nextval('public.billing_fichefacturation_id_seq'::regclass);


--
-- Name: billing_ficheitem id; Type: DEFAULT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_ficheitem ALTER COLUMN id SET DEFAULT nextval('public.billing_ficheitem_id_seq'::regclass);


--
-- Name: billing_fichefacturation billing_fichefacturation_pkey; Type: CONSTRAINT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_fichefacturation
    ADD CONSTRAINT billing_fichefacturation_pkey PRIMARY KEY (id);


--
-- Name: billing_ficheitem billing_ficheitem_pkey; Type: CONSTRAINT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_ficheitem
    ADD CONSTRAINT billing_ficheitem_pkey PRIMARY KEY (id);


--
-- Name: billing_fichefacturation_client_id_9b6baa52; Type: INDEX; Schema: public; Owner: mkhaled
--

CREATE INDEX billing_fichefacturation_client_id_9b6baa52 ON public.billing_fichefacturation USING btree (client_id);


--
-- Name: billing_fichefacturation_owner_id_4556f05f; Type: INDEX; Schema: public; Owner: mkhaled
--

CREATE INDEX billing_fichefacturation_owner_id_4556f05f ON public.billing_fichefacturation USING btree (owner_id);


--
-- Name: billing_ficheitem_dossier_id_14584a4f; Type: INDEX; Schema: public; Owner: mkhaled
--

CREATE INDEX billing_ficheitem_dossier_id_14584a4f ON public.billing_ficheitem USING btree (dossier_id);


--
-- Name: billing_ficheitem_fich_id_798951a9; Type: INDEX; Schema: public; Owner: mkhaled
--

CREATE INDEX billing_ficheitem_fich_id_798951a9 ON public.billing_ficheitem USING btree (fich_id);


--
-- Name: billing_fichefacturation billing_fichefacturation_client_id_9b6baa52_fk; Type: FK CONSTRAINT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_fichefacturation
    ADD CONSTRAINT billing_fichefacturation_client_id_9b6baa52_fk FOREIGN KEY (client_id) REFERENCES public.relations_client(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: billing_fichefacturation billing_fichefacturation_owner_id_4556f05f_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_fichefacturation
    ADD CONSTRAINT billing_fichefacturation_owner_id_4556f05f_fk_auth_user_id FOREIGN KEY (owner_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: billing_ficheitem billing_ficheitem_dossier_id_14584a4f_fk_operations_dossier_id; Type: FK CONSTRAINT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_ficheitem
    ADD CONSTRAINT billing_ficheitem_dossier_id_14584a4f_fk_operations_dossier_id FOREIGN KEY (dossier_id) REFERENCES public.operations_dossier(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: billing_ficheitem billing_ficheitem_fich_id_798951a9_fk_billing_f; Type: FK CONSTRAINT; Schema: public; Owner: mkhaled
--

ALTER TABLE ONLY public.billing_ficheitem
    ADD CONSTRAINT billing_ficheitem_fich_id_798951a9_fk_billing_f FOREIGN KEY (fich_id) REFERENCES public.billing_fichefacturation(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

